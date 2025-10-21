# -*- coding: utf-8 -*-
# مراكز تقريبية (LAT, LON) لأشهر ولايات عُمان لاستخدامها كمرجع إداري مبسّط.
# الهدف: إسناد (محافظة/ولاية) لأية نقطة عبر أقرب مركز.
import math

WILAYA_CENTROIDS = [
    # Muscat Governorate
    ("Muscat", "Muscat",      23.588, 58.407),
    ("Muscat", "Seeb",        23.669, 58.190),
    ("Muscat", "Bawshar",     23.555, 58.405),
    ("Muscat", "Muttrah",     23.617, 58.567),
    ("Muscat", "Al Amerat",   23.473, 58.520),
    ("Muscat", "Qurayyat",    23.264, 58.919),

    # Dhofar
    ("Dhofar", "Salalah",     17.019, 54.099),
    ("Dhofar", "Thumrait",    17.666, 54.028),
    ("Dhofar", "Taqah",       17.043, 54.371),
    ("Dhofar", "Mirbat",      16.992, 54.689),

    # Al Wusta
    ("Al Wusta", "Duqm",      19.647, 57.735),
    ("Al Wusta", "Hayma",     19.957, 56.275),
    ("Al Wusta", "Mahout",    20.744, 58.871),

    # Al Dhahirah
    ("Al Dhahirah", "Ibri",   23.225, 56.515),
    ("Al Dhahirah", "Yanqul", 23.587, 56.541),
    ("Al Dhahirah", "Dhank",  23.462, 56.249),

    # North Al Batinah
    ("North Al Batinah", "Sohar",     24.347, 56.707),
    ("North Al Batinah", "Shinas",    24.743, 56.466),
    ("North Al Batinah", "Liwa",      24.530, 56.562),
    ("North Al Batinah", "Saham",     24.172, 56.888),
    ("North Al Batinah", "Al Khaburah", 23.981, 57.100),
    ("North Al Batinah", "Suwaiq",    23.849, 57.438),

    # South Al Batinah
    ("South Al Batinah", "Barka",     23.707, 57.889),
    ("South Al Batinah", "Rustaq",    23.389, 57.424),
    ("South Al Batinah", "Al Awabi",  23.394, 57.396),
    ("South Al Batinah", "Nakhal",    23.397, 57.829),
    ("South Al Batinah", "Wadi Al Maawil", 23.460, 57.787),
    ("South Al Batinah", "Al Musannah", 23.659, 57.890),

    # North Al Sharqiyah
    ("North Al Sharqiyah", "Ibra",       22.713, 58.533),
    ("North Al Sharqiyah", "Al Mudhaibi", 22.575, 58.160),
    ("North Al Sharqiyah", "Bidiyah",    22.453, 58.800),

    # South Al Sharqiyah
    ("South Al Sharqiyah", "Sur",             22.566, 59.528),
    ("South Al Sharqiyah", "Jalan Bani Bu Ali", 22.000, 59.450),
    ("South Al Sharqiyah", "Jalan Bani Bu Hassan", 22.105, 59.317),
    ("South Al Sharqiyah", "Masirah",         20.485, 58.799),

    # Al Dakhiliyah
    ("Al Dakhiliyah", "Nizwa",  22.933, 57.533),
    ("Al Dakhiliyah", "Bahla",  22.967, 57.300),
    ("Al Dakhiliyah", "Adam",   22.390, 57.533),
    ("Al Dakhiliyah", "Izki",   22.938, 57.766),
    ("Al Dakhiliyah", "Manah",  22.793, 57.587),
    ("Al Dakhiliyah", "Samail", 23.304, 58.016),
    ("Al Dakhiliyah", "Al Hamra", 23.116, 57.285),

    # Musandam
    ("Musandam", "Khasab", 26.179, 56.247),
    ("Musandam", "Bukha",  26.197, 56.355),
    ("Musandam", "Dibba",  25.615, 56.265),

    # Al Buraimi
    ("Al Buraimi", "Al Buraimi", 24.253, 55.793),
    ("Al Buraimi", "Mahdah",     24.200, 55.970),
]

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlbd = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlbd/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def assign_wilaya_from_point(lat, lon):
    """أقرب ولاية (ومحافظتها) بناءً على الإحداثيات."""
    best = None
    best_d = 1e9
    for gov, wil, la, lo in WILAYA_CENTROIDS:
        d = haversine_km(lat, lon, la, lo)
        if d < best_d:
            best_d = d
            best = (gov, wil)
    return best  # (governorate, wilaya)
