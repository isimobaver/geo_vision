# geoeco/geo/oman_polygon.py
# ملاحظة: القيم تقريبية ومبسطة للاستخدام البرمجي التجريبي فقط.

from random import uniform

# كل نقطة = (lat, lon)
OMAN_MAINLAND = [
    (26.0, 56.05), (25.6, 56.50), (25.0, 56.65), (24.4, 56.35), (23.9, 55.9),
    (23.6, 55.3),  (23.1, 55.2),  (22.4, 55.0),  (21.7, 55.0),  (20.8, 55.0),
    (19.7, 55.2),  (19.2, 55.6),  (18.4, 55.8),  (17.8, 55.5),  (17.4, 55.1),
    (17.1, 54.6),  (17.0, 54.2),  (17.1, 53.8),  (17.4, 53.5),  (17.7, 53.4),
    (18.3, 53.5),  (19.0, 53.9),  (19.8, 54.4),  (20.4, 54.7),  (21.2, 55.2),
    (22.2, 55.6),  (23.0, 55.9),  (23.7, 56.2),  (24.5, 56.6),  (25.2, 56.8),
    (25.7, 56.6),  (26.0, 56.05)  # إغلاق المضلع
]

OMAN_MUSANDAM = [
    (26.4, 56.15), (26.35, 56.3), (26.25, 56.45), (26.15, 56.4),
    (26.05, 56.25), (26.1, 56.1), (26.2, 56.05), (26.3, 56.05),
    (26.4, 56.15)  # إغلاق المضلع
]

OMAN_POLYGONS = [OMAN_MAINLAND, OMAN_MUSANDAM]

def point_in_poly(lat, lon, poly):
    """Ray-casting algorithm: True if (lat, lon) inside polygon."""
    inside = False
    n = len(poly)
    for i in range(n):
        y1, x1 = poly[i]
        y2, x2 = poly[(i + 1) % n]
        # هل يعبر الشعاع الأُفقي بين الضلع؟
        if ((x1 > lon) != (x2 > lon)):
            # نقطة التقاطع مع خط العرض
            lat_at_lon = (y2 - y1) * (lon - x1) / (x2 - x1 + 1e-12) + y1
            if lat_at_lon > lat:
                inside = not inside
    return inside

def point_in_oman(lat, lon):
    return any(point_in_poly(lat, lon, poly) for poly in OMAN_POLYGONS)

def bbox_of(poly):
    lats = [p[0] for p in poly]
    lons = [p[1] for p in poly]
    return min(lats), max(lats), min(lons), max(lons)

BBOXES = [bbox_of(p) for p in OMAN_POLYGONS]

def random_point_in_polygon(poly, max_tries=5000):
    min_la, max_la, min_lo, max_lo = bbox_of(poly)
    for _ in range(max_tries):
        la = round(uniform(min_la, max_la), 6)
        lo = round(uniform(min_lo, max_lo), 6)
        if point_in_poly(la, lo, poly):
            return la, lo
    raise RuntimeError("Failed to sample point inside polygon")

def random_point_in_oman():
    # اختَر مضلعًا عشوائيًا (وزن مبسط: المسندم أصغر، لكن لا بأس)
    poly = OMAN_MAINLAND if uniform(0,1) > 0.1 else OMAN_MUSANDAM
    return random_point_in_polygon(poly)
