# geoeco/management/commands/generate_bulk_data.py
import random
from datetime import date, datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from geoeco.models import Company, Mineral, Site, ProductionMetric, EnvironmentalMetric, License, Alert

GOVS = [
    "Muscat", "Dhofar", "Al Wusta", "Al Buraimi", "Al Dhahirah",
    "North Al Batinah", "South Al Batinah", "North Al Sharqiyah",
    "South Al Sharqiyah", "Al Dakhiliyah", "Musandam"
]

MINERALS = [
    ("Copper", "ton"), ("Chromite", "ton"), ("Gypsum", "ton"),
    ("Limestone", "ton"), ("Gold", "kg"), ("Manganese", "ton"),
    ("Silica", "ton"), ("Dolomite", "ton")
]

def rand_coord(governorate: str):
    # نطاقات تقريبية داخل عُمان (تبسيط)
    lat = random.uniform(16.8, 26.5)
    lon = random.uniform(52.0, 59.9)
    return round(lat, 6), round(lon, 6)

class Command(BaseCommand):
    help = "Generate a large synthetic dataset for GeoEco Tracker"

    def add_arguments(self, parser):
        parser.add_argument("--companies", type=int, default=40)
        parser.add_argument("--sites", type=int, default=600)
        parser.add_argument("--years", type=int, default=8, help="how many past years of production to create")
        parser.add_argument("--monthly_readings", type=int, default=24, help="environment readings per site")
        parser.add_argument("--alerts_per_site", type=int, default=2)
        parser.add_argument("--seed", type=int, default=2025)
        parser.add_argument("--wipe", action="store_true", help="delete ALL existing demo data first")

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"])
        companies_n = opts["companies"]
        sites_n = opts["sites"]
        years_n = opts["years"]
        monthly_n = opts["monthly_readings"]
        alerts_n = opts["alerts_per_site"]
        wipe = opts["wipe"]

        if wipe:
            self.stdout.write(self.style.WARNING("Wiping existing demo data..."))
            Alert.objects.all().delete()
            EnvironmentalMetric.objects.all().delete()
            ProductionMetric.objects.all().delete()
            License.objects.all().delete()
            Site.objects.all().delete()
            Company.objects.all().delete()
            Mineral.objects.all().delete()

        # Minerals
        minerals = {}
        for name, unit in MINERALS:
            m, _ = Mineral.objects.get_or_create(name=name, defaults={"unit": unit})
            minerals[name] = m

        # Companies
        self.stdout.write(f"Creating ~{companies_n} companies...")
        comps = []
        for i in range(companies_n):
            c = Company.objects.create(
                name=f"Company {i+1:03d}",
                sustainability_score=round(random.uniform(55, 95), 2),
            )
            comps.append(c)

        # Sites
        self.stdout.write(f"Creating ~{sites_n} sites + licenses...")
        all_sites = []
        for i in range(sites_n):
            gov = random.choice(GOVS)
            mineral = random.choice(list(minerals.values()))
            company = random.choice(comps)
            status = random.choices(["active", "proposed", "closed"], weights=[0.55, 0.3, 0.15])[0]
            band = random.choices(["green", "yellow", "red"], weights=[0.5, 0.35, 0.15])[0]
            lat, lon = rand_coord(gov)

            s = Site.objects.create(
                name=f"{gov} {mineral.name} Site {i+1:04d}",
                company=company,
                mineral=mineral,
                status=status,
                sustainability_band=band,
                governorate=gov,
                lat=lat, lon=lon,
            )
            all_sites.append(s)

            # License (بسيطة لكل موقع)
            issued = date.today().replace(year=date.today().year - random.randint(0, 5))
            expires = issued.replace(year=issued.year + random.randint(3, 7))
            License.objects.create(
                site=s,
                license_no=f"OM-{issued.year}-{mineral.name[:3].upper()}-{i+1:05d}",
                issued_on=issued,
                expires_on=expires,
            )

        # Production per year
        self.stdout.write("Creating production metrics...")
        current_year = date.today().year
        for s in all_sites:
            base = random.uniform(200, 1_500_000)  # tons or kg depending on mineral
            # أبقِ الذهب أصغر حجمًا
            if s.mineral.unit == "kg":
                base = random.uniform(5, 2_000)

            for k in range(years_n):
                y = current_year - k
                # نمو/انكماش طفيف
                q = max(0, random.gauss(base * (1 - k * 0.02), base * 0.1))
                ProductionMetric.objects.update_or_create(
                    site=s, year=y, defaults={"quantity": round(q, 2)}
                )

        # Environmental metrics (monthly_n أحدث قراءات شهرية تقريبًا لكل موقع)
        self.stdout.write("Creating environmental metrics...")
        for s in all_sites:
            start_dt = timezone.now() - timedelta(days=30 * monthly_n)
            for m in range(monthly_n):
                dt = start_dt + timedelta(days=30 * m + random.randint(0, 5))
                aqi = max(20, min(120, random.gauss(55 if s.sustainability_band == "green" else (70 if s.sustainability_band == "yellow" else 85), 10)))
                tds = max(300, min(1600, random.gauss(550 if s.sustainability_band == "green" else (800 if s.sustainability_band == "yellow" else 1050), 120)))
                rehab = max(0, min(100, random.gauss(60 if s.status == "active" else 30, 20)))
                EnvironmentalMetric.objects.create(
                    site=s,
                    date=dt.date(),
                    air_quality_index=round(aqi, 1),
                    water_tds=round(tds, 1),
                    rehabilitation_progress=round(rehab, 1),
                )

        # Alerts
        self.stdout.write("Creating alerts...")
        for s in all_sites:
            for _ in range(alerts_n):
                level = random.choices(["info", "warn", "critical"], weights=[0.6, 0.3, 0.1])[0]
                msg = random.choice([
                    "مستويات الغبار ضمن الحدود.",
                    "مطلوب صيانة فلاتر الأتربة.",
                    "ارتفاع مؤقت في TDS بالمياه الجوفية.",
                    "تحسّن مؤشر جودة الهواء.",
                    "انسكاب بسيط تحت الاحتواء.",
                    "تجاوز حد TDS — إيقاف مؤقت للمضخات."
                ])
                created_at = timezone.now() - timedelta(days=random.randint(0, 365))
                Alert.objects.create(site=s, level=level, message=msg, created_at=created_at)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Companies={Company.objects.count()}, Sites={Site.objects.count()}, "
            f"Prod={ProductionMetric.objects.count()}, Env={EnvironmentalMetric.objects.count()}, Alerts={Alert.objects.count()}"
        ))
