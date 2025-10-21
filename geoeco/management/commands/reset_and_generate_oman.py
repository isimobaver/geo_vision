# -*- coding: utf-8 -*-
import math
import json
import random
from collections import defaultdict
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from geoeco.models import (
    Company, Mineral, Site,
    ProductionMetric, EnvironmentalMetric, License, Alert
)

# مضلعات المناطق الواعدة + مولّد نقطة داخل المضلع
from geoeco.geo.oman_hotspots import (
    HOTSPOT_POLYGONS,         # dict: key -> {"poly": [(lat,lon),...], "weight": float, "minerals": [names]}
    random_point_in_polygon,  # يعيد (lat,lon) داخل المضلع
)

# تأكيد أن النقطة داخل اليابسة ضمن حدود سلطنة عُمان (لا بحر ولا خارج الحدود)
from geoeco.geo.oman_polygon import point_in_oman

# إسناد المحافظة/الولاية من الإحداثيات (أقرب سنترُويد لولاية)
from geoeco.geo.oman_admin import assign_wilaya_from_point


# أسماء المحافظات (للاستخدام العام عند الحاجة)
GOVS = [
    "Muscat","Dhofar","Al Wusta","Al Buraimi","Al Dhahirah",
    "North Al Batinah","South Al Batinah","North Al Sharqiyah",
    "South Al Sharqiyah","Al Dakhiliyah","Musandam"
]

# تعريف المعادن + وحداتها
MINERALS_DEF = [
    ("Copper","ton"), ("Chromite","ton"), ("Gypsum","ton"),
    ("Limestone","ton"), ("Gold","kg"), ("Manganese","ton"),
    ("Silica","ton"), ("Dolomite","ton"),
]

# تفضيل عام لأنواع المعادن (يُركّز على الحجر الجيري وما شابه)
GLOBAL_MINERAL_WEIGHTS = {
    "Copper": 1.10, "Chromite": 1.00, "Gold": 0.45, "Gypsum": 1.10,
    "Limestone": 1.60, "Silica": 1.00, "Dolomite": 0.85, "Manganese": 0.55,
}

# أهداف وطنية تقريبية سنوية (بالطن) لمعادلة المجاميع
DEFAULT_TARGETS_TONNES = {
    "Limestone": 25_000_000,
    "Gypsum":    10_000_000,
    "Silica":     1_000_000,
    "Dolomite":     800_000,
    "Manganese":    150_000,
    "Chromite":     900_000,
    "Copper":       200_000,
}
# الذهب بالكيلوغرام
DEFAULT_TARGETS_KG = {
    "Gold": 1_500,  # 1.5 طن ≈ 1500 كغ
}

# حدود مبدئية لإنتاج الموقع الواحد قبل التسوية (لكل سنة أحدث)
INITIAL_PER_SITE_RANGES = {
    "Limestone": (80_000, 450_000),
    "Gypsum":    (60_000, 350_000),
    "Silica":    (10_000,  60_000),
    "Dolomite":  (10_000,  50_000),
    "Manganese": ( 3_000,  25_000),
    "Chromite":  ( 5_000,  60_000),
    "Copper":    ( 3_000,  35_000),
    "Gold":      ( 8,      260),     # بالكيلو
}


# ======= أدوات مساعدة =======

def haversine_km(lat1, lon1, lat2, lon2):
    """المسافة الكبرى على سطح الأرض بالكيلومترات."""
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlbd = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlbd/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def place_points_spread(poly, target_n, min_km, max_tries=8000):
    """
    توليد نقاط داخل مضلع مع حد أدنى للمسافة (بدون تكتّل)،
    مع التأكد أنها داخل اليابسة ضمن حدود سلطنة عُمان.
    """
    pts = []
    tries = 0
    while len(pts) < target_n and tries < max_tries:
        tries += 1
        la, lo = random_point_in_polygon(poly)
        # لا بحر ولا خارج الحدود
        if not point_in_oman(la, lo):
            continue
        # شرط التباعد الأدنى
        if all(haversine_km(la, lo, a, b) >= min_km for (a, b) in pts):
            pts.append((la, lo))
    return pts

def rand_range(a, b):
    """قيمة عشوائية ملساء بين a..b (باستخدام log-uniform + ضجيج) لواقعية أعلى."""
    base = math.exp(random.uniform(math.log(max(1, a)), math.log(max(1, b))))
    return max(a, min(b, random.gauss(base, base * 0.12)))


# ======= أمر الإدارة =======

class Command(BaseCommand):
    help = "Regenerate realistic Oman sites (land only), spaced-out, wilaya-mapped, and production calibrated to national targets."

    def add_arguments(self, parser):
        parser.add_argument("--sites", type=int, default=800)
        parser.add_argument("--companies", type=int, default=55)
        parser.add_argument("--years", type=int, default=10)
        parser.add_argument("--monthly", type=int, default=24)
        parser.add_argument("--alerts", type=int, default=2)
        parser.add_argument("--seed", type=int, default=2025)
        parser.add_argument("--wipe_companies", action="store_true")
        parser.add_argument("--min_km", type=float, default=10.0, help="أقل مسافة بين موقعين داخل نفس المضلع (كم)")
        parser.add_argument("--per_poly_floor", type=int, default=12, help="حد أدنى للمواقع لكل مضلع Hotspot")
        parser.add_argument("--targets-json", type=str, default="", help="JSON لتخصيص الأهداف الوطنية (tonnes/kg)")

    @transaction.atomic
    def handle(self, *args, **o):
        random.seed(o["seed"])
        sites_n = o["sites"]; companies_n = o["companies"]
        years_n = o["years"]; monthly_n = o["monthly"]; alerts_n = o["alerts"]
        min_km = o["min_km"]; per_poly_floor = o["per_poly_floor"]

        # تحميل أهداف وطنية مخصّصة إن وُجدت
        targets_tonnes = DEFAULT_TARGETS_TONNES.copy()
        targets_kg = DEFAULT_TARGETS_KG.copy()
        if o["targets_json"]:
            try:
                user_targets = json.loads(o["targets_json"])
                targets_tonnes.update(user_targets.get("tonnes", {}))
                targets_kg.update(user_targets.get("kg", {}))
            except Exception:
                self.stdout.write(self.style.WARNING("لم يُفك ترميز --targets-json؛ سيتم استخدام القيم الافتراضية."))

        # مسح البيانات القديمة
        self.stdout.write(self.style.WARNING("Deleting ALL sites & related data…"))
        Alert.objects.all().delete()
        EnvironmentalMetric.objects.all().delete()
        ProductionMetric.objects.all().delete()
        License.objects.all().delete()
        Site.objects.all().delete()

        # اختيارياً مسح الشركات/المعادن
        if o["wipe_companies"]:
            Company.objects.all().delete()
            Mineral.objects.all().delete()

        # معادن/شركات
        minerals = {}
        for name, unit in MINERALS_DEF:
            m, _ = Mineral.objects.get_or_create(name=name, defaults={"unit": unit})
            minerals[name] = m

        comps = list(Company.objects.all())
        while len(comps) < companies_n:
            idx = len(comps) + 1
            comps.append(
                Company.objects.create(
                    name=f"Company {idx:03d}",
                    sustainability_score=round(random.uniform(60, 92), 2)
                )
            )

        # توزيع عدد المواقع على المضلعات بحسب الأوزان + حد أدنى لكل مضلع
        items = list(HOTSPOT_POLYGONS.items())  # [(key, meta), ...]
        weights = [meta["weight"] for _, meta in items]
        weight_sum = sum(weights) if sum(weights) > 0 else 1.0

        targets = {key: per_poly_floor for key, _ in items}
        remaining = max(0, sites_n - per_poly_floor * len(items))
        for key, meta in items:
            if remaining <= 0:
                break
            share = int(round(remaining * (meta["weight"] / weight_sum)))
            targets[key] += share

        # تصحيح فروق التقريب
        diff = sites_n - sum(targets.values())
        if diff != 0:
            keys = list(targets.keys())
            for i in range(abs(diff)):
                k = keys[i % len(keys)]
                targets[k] += 1 if diff > 0 else -1

        # توليد نقاط متباعدة داخل كل مضلع (يابسة فقط)
        self.stdout.write("Generating spaced points per hotspot polygon…")
        poly_points = {}
        for key, meta in items:
            poly = meta["poly"]
            need = max(0, targets[key])
            pts = place_points_spread(poly, target_n=need, min_km=min_km, max_tries=need * 600)
            if len(pts) < need:
                self.stdout.write(self.style.WARNING(
                    f"[{key}] لم نتمكن من توليد كل النقاط المطلوبة مع min_km={min_km}. "
                    f"تم توليد {len(pts)}/{need}."
                ))
            poly_points[key] = pts

        # إنشاء المواقع + إسناد المحافظة/الولاية من الإحداثيات + اختيار معدن منطقي لكل مضلع
        created_sites = []
        self.stdout.write("Creating sites + licenses…")
        for key, pts in poly_points.items():
            allowed = HOTSPOT_POLYGONS[key]["minerals"]

            # أوزان محلية: تفضيل المعادن المسموحة في هذا المضلع
            local_names = list(minerals.keys())
            local_w = []
            for mname in local_names:
                w = GLOBAL_MINERAL_WEIGHTS.get(mname, 1.0)
                w *= 1.8 if mname in allowed else 0.30
                local_w.append(w)

            for (lat, lon) in pts:
                mineral_name = random.choices(local_names, weights=local_w, k=1)[0]
                mineral = minerals[mineral_name]

                # ⬅️ إسناد المحافظة/الولاية من الإحداثيات
                governorate, wilaya = assign_wilaya_from_point(lat, lon)

                # حالة واستدامة
                status = random.choices(["active","proposed","closed"], weights=[0.64, 0.31, 0.05])[0]
                if mineral_name in ("Limestone","Gypsum","Silica","Dolomite"):
                    band_w = [0.62, 0.32, 0.06]
                elif mineral_name in ("Copper","Chromite","Manganese"):
                    band_w = [0.52, 0.36, 0.12]
                else:  # Gold
                    band_w = [0.50, 0.36, 0.14]
                band = random.choices(["green","yellow","red"], weights=band_w, k=1)[0]

                # دعم اختياري لحقل wilaya إن كان موجودًا في الموديل
                site_kwargs = dict(
                    name=f"{governorate} {mineral.name} Site {len(created_sites)+1:05d}",
                    company=random.choice(comps),
                    mineral=mineral,
                    status=status,
                    sustainability_band=band,
                    lat=lat, lon=lon,
                    governorate=governorate,
                )
                site_fields = {f.name for f in Site._meta.get_fields()}
                if "wilaya" in site_fields:
                    site_kwargs["wilaya"] = wilaya

                s = Site.objects.create(**site_kwargs)
                created_sites.append(s)

                issued = date.today().replace(year=date.today().year - random.randint(0, 4))
                expires = issued.replace(year=issued.year + random.randint(4, 8))
                License.objects.create(
                    site=s,
                    license_no=f"OM-{issued.year}-{mineral.name[:3].upper()}-{len(created_sites):06d}",
                    issued_on=issued,
                    expires_on=expires
                )

        # توليد إنتاج سنوي مبدئي لكل موقع (سنة حديثة)، ثم معايرة إلى الأهداف الوطنية
        self.stdout.write("Generating initial (pre-calibration) production time series…")
        current_year = date.today().year
        latest_year = current_year

        sum_by_mineral_latest = defaultdict(float)  # مجموع أحدث سنة لكل معدن
        site_latest_values = {}                     # site_id -> latest_value (طن، والذهب بالكيلو)

        for s in created_sites:
            mname = s.mineral.name
            low, high = INITIAL_PER_SITE_RANGES[mname]
            val_latest = rand_range(low, high)
            site_latest_values[s.id] = val_latest
            sum_by_mineral_latest[mname] += val_latest

        # معاملات التسوية لتقريب المجاميع من الأهداف الوطنية
        factor_by_mineral = {}
        for mname in {s.mineral.name for s in created_sites}:
            total_latest = sum_by_mineral_latest.get(mname, 0.0) or 1.0
            if mname == "Gold":
                target = float(targets_kg.get("Gold", DEFAULT_TARGETS_KG["Gold"]))
            else:
                target = float(targets_tonnes.get(mname, total_latest))
            factor_by_mineral[mname] = max(0.1, target / total_latest)

        # إنشاء السلاسل الزمنية السنوية بعد التسوية (انحدار بسيط للخلف + ضجيج خفيف)
        for s in created_sites:
            mname = s.mineral.name
            f = factor_by_mineral[mname]
            base_latest = site_latest_values[s.id] * f

            for k in range(years_n):
                y = current_year - k
                drift = (1 - 0.012 * k)             # تناقص طفيف كل سنة
                noise = random.gauss(1.0, 0.08)      # ضجيج بسيط
                val = max(0, base_latest * drift * noise)
                ProductionMetric.objects.create(
                    site=s, year=y,
                    quantity=round(val, 2)
                )

        # قياسات بيئية شهرية واقعية بحسب الخام وشريحة الاستدامة
        self.stdout.write("Generating environmental metrics…")
        for s in created_sites:
            start = timezone.now() - timedelta(days=30 * monthly_n)

            # أساسات حسب نوع الخام
            if s.mineral.name in ("Limestone","Gypsum","Silica","Dolomite"):
                aqi_base0 = 55
                tds_base0 = 560
            elif s.mineral.name in ("Copper","Chromite","Manganese"):
                aqi_base0 = 65
                tds_base0 = 760
            else:  # Gold
                aqi_base0 = 60
                tds_base0 = 700

            # تعديل حسب شريحة الاستدامة
            if s.sustainability_band == "green":
                aqi_base = aqi_base0 - 5
                tds_base = tds_base0 - 40
            elif s.sustainability_band == "yellow":
                aqi_base = aqi_base0 + 5
                tds_base = tds_base0 + 60
            else:  # red
                aqi_base = aqi_base0 + 15
                tds_base = tds_base0 + 160

            rehab = 68 if s.status == "active" else 35

            for m in range(monthly_n):
                dt = start + timedelta(days=30 * m + random.randint(0, 5))
                EnvironmentalMetric.objects.create(
                    site=s,
                    date=dt.date(),
                    air_quality_index=round(max(20, min(135, random.gauss(aqi_base, 8))), 1),
                    water_tds=round(max(300, min(1700, random.gauss(tds_base, 100))), 1),
                    rehabilitation_progress=round(max(0, min(100, random.gauss(rehab, 16))), 1),
                )

        # تنبيهات بسيطة
        self.stdout.write("Generating alerts…")
        for s in created_sites:
            for _ in range(alerts_n):
                level = random.choices(["info","warn","critical"], weights=[0.66, 0.25, 0.09])[0]
                msg = random.choice([
                    "مستويات الغبار ضمن الحدود.",
                    "مطلوب صيانة فلاتر الأتربة.",
                    "تحسّن في مؤشر جودة الهواء.",
                    "ارتفاع مؤقت في TDS بالمياه الجوفية.",
                    "تسرّب بسيط تحت الاحتواء.",
                    "تجاوز TDS — إيقاف مؤقت للمضخات."
                ])
                Alert.objects.create(
                    site=s, level=level, message=msg,
                    created_at=timezone.now() - timedelta(days=random.randint(0, 360))
                )

        self.stdout.write(self.style.SUCCESS(
            f"Done ✅  Sites={Site.objects.count()}  "
            f"Prod={ProductionMetric.objects.count()}  "
            f"Env={EnvironmentalMetric.objects.count()}  "
            f"Alerts={Alert.objects.count()}"
        ))
