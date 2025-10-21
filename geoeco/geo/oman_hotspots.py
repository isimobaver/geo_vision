# geoeco/geo/oman_hotspots.py
# مضلعات مبسطة لمناطق واعدة في عُمان (تقريبية لأغراض العرض/demo)
# الإحداثيات بالترتيب (lat, lon) ويجب إغلاق المضلع بتكرار أول نقطة في النهاية.

import random

def point_in_poly(lat, lon, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        y1, x1 = poly[i]
        y2, x2 = poly[(i + 1) % n]
        if ((x1 > lon) != (x2 > lon)):
            lat_at_lon = (y2 - y1) * (lon - x1) / (x2 - x1 + 1e-12) + y1
            if lat_at_lon > lat:
                inside = not inside
    return inside

def bbox(poly):
    lats = [p[0] for p in poly]; lons = [p[1] for p in poly]
    return min(lats), max(lats), min(lons), max(lons)

def random_point_in_polygon(poly, max_tries=4000):
    la1, la2, lo1, lo2 = bbox(poly)
    for _ in range(max_tries):
        la = round(random.uniform(la1, la2), 6)
        lo = round(random.uniform(lo1, lo2), 6)
        if point_in_poly(la, lo, poly):
            return la, lo
    raise RuntimeError("Failed to sample point in polygon")

# ========= مضلعات مبسطة =========

# 1) الأوفيولايت (شريط داخلي من شمال الباطنة للظاهرة) – نحاس/كروميت/ذهب
SEMAIL_OPHIOLITE = [
    (24.90, 57.55), (24.50, 57.30), (24.10, 57.00), (23.70, 56.70),
    (23.30, 56.40), (22.90, 56.10), (22.70, 55.90), (22.70, 55.70),
    (23.10, 55.70), (23.60, 56.00), (24.00, 56.30), (24.40, 56.60),
    (24.80, 57.20), (24.95, 57.45), (24.90, 57.55)
]

# 2) إبــرى/شمال الشرقية – كروميت
IBRA_CHROMITE = [
    (23.10, 58.10), (22.90, 58.10), (22.60, 58.30), (22.45, 58.70),
    (22.60, 59.05), (22.85, 59.20), (23.05, 59.05), (23.15, 58.70),
    (23.15, 58.40), (23.10, 58.10)
]

# 3) ينقل/الظاهرة – ذهب/نحاس
YANQUL_GOLD = [
    (23.95, 56.55), (23.80, 56.40), (23.55, 56.35), (23.45, 56.45),
    (23.45, 56.65), (23.65, 56.80), (23.85, 56.80), (23.95, 56.65),
    (23.95, 56.55)
]

# 4) ظفار (صلالة/ثمريت) – جبس
DHOFAR_GYPSUM = [
    (18.10, 54.45), (17.90, 54.25), (17.65, 54.10), (17.40, 54.05),
    (17.20, 54.20), (17.15, 54.45), (17.25, 54.65), (17.55, 54.75),
    (17.85, 54.70), (18.05, 54.55), (18.10, 54.45)
]

# 5) الدقم/وسطى – حجر جيري/سيليكا/دولومايت
DUQM_CARBONATES = [
    (21.30, 58.10), (21.00, 57.80), (20.50, 57.50), (20.10, 57.40),
    (19.70, 57.60), (19.60, 57.90), (19.80, 58.30), (20.20, 58.55),
    (20.70, 58.60), (21.10, 58.45), (21.30, 58.10)
]

# 6) صــور/جنوب الشرقية – حجر جيري/سيليكا
SUR_LIMESTONE = [
    (22.95, 59.80), (22.75, 59.70), (22.55, 59.65), (22.40, 59.70),
    (22.30, 59.85), (22.35, 60.00), (22.55, 60.10), (22.80, 60.05),
    (22.95, 59.90), (22.95, 59.80)
]

# 7) مسندم (اختياري لقلة المساحة التعدينية الفعلية) – نادراً ما نستخدمه
MUSANDAM_SMALL = [
    (26.30, 56.25), (26.22, 56.28), (26.16, 56.35), (26.14, 56.45),
    (26.20, 56.50), (26.28, 56.45), (26.35, 56.35), (26.34, 56.28),
    (26.30, 56.25)
]

HOTSPOT_POLYGONS = {
    "SEMAIL_OPHIOLITE": {
        "poly": SEMAIL_OPHIOLITE,
        "minerals": ["Copper", "Chromite", "Gold"],
        "weight": 4.0
    },
    "IBRA_CHROMITE": {
        "poly": IBRA_CHROMITE,
        "minerals": ["Chromite"],
        "weight": 3.0
    },
    "YANQUL_GOLD": {
        "poly": YANQUL_GOLD,
        "minerals": ["Gold", "Copper"],
        "weight": 2.5
    },
    "DHOFAR_GYPSUM": {
        "poly": DHOFAR_GYPSUM,
        "minerals": ["Gypsum"],
        "weight": 4.0
    },
    "DUQM_CARBONATES": {
        "poly": DUQM_CARBONATES,
        "minerals": ["Limestone", "Silica", "Dolomite"],
        "weight": 3.5
    },
    "SUR_LIMESTONE": {
        "poly": SUR_LIMESTONE,
        "minerals": ["Limestone", "Silica"],
        "weight": 2.0
    },
    "MUSANDAM_SMALL": {
        "poly": MUSANDAM_SMALL,
        "minerals": ["Limestone"],  # قليلة الاستخدام
        "weight": 0.2
    }
}

# اختيار مضلع مناسب لمعدن معيّن
def polygons_for_mineral(mineral_name):
    polys = []
    for name, meta in HOTSPOT_POLYGONS.items():
        if mineral_name in meta["minerals"]:
            polys.append((name, meta))
    return polys

def random_point_for_mineral(mineral_name):
    """اختر مضلعاً مناسباً للمعدن وفق الأوزان ثم عيّن نقطة داخله"""
    candidates = polygons_for_mineral(mineral_name)
    if not candidates:
        # fallback: اختر أي مضلع بوزنه
        items = list(HOTSPOT_POLYGONS.items())
        weights = [m["weight"] for _, m in items]
        name, meta = random.choices(items, weights=weights, k=1)[0]
        return random_point_in_polygon(meta["poly"])
    weights = [meta["weight"] for _, meta in candidates]
    name, meta = random.choices(candidates, weights=weights, k=1)[0]
    return random_point_in_polygon(meta["poly"])

def cluster_point_in_polygon(poly, centers=None, spread_km=15.0):
    """
    توليد نقاط متكتلة: نختار مركزًا (seed) ثم نذبذب حوله قليلاً.
    spread_km ~6 كم تقريبًا => ~0.06 درجة تقريبية (تقريب شديد)
    """
    if not centers:
        # أنشئ مركزًا عشوائيًا داخل المضلع
        c_lat, c_lon = random_point_in_polygon(poly)
    else:
        c_lat, c_lon = random.choice(centers)

    # 1 درجة ≈ 111 كم. 6 كم ≈ 0.054 درجة تقريبًا.
    delta = spread_km / 111.0
    for _ in range(200):
        la = round(c_lat + random.uniform(-delta, delta), 6)
        lo = round(c_lon + random.uniform(-delta, delta), 6)
        if point_in_poly(la, lo, poly):
            return la, lo
    # fallback
    return random_point_in_polygon(poly)
