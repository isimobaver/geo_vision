# geoeco/services/band_logic.py

def clip(x, lo, hi):
    return max(lo, min(hi, x))

def band_from_env(aqi, tds, rehab, status):
    # تحويل الدرجات إلى 0..100
    aqi_score  = clip(100 - (aqi - 40) * 1.2, 0, 100)      # كلما زاد AQI ساءت الدرجة
    tds_score  = clip(100 - (tds - 500) * 0.08, 0, 100)    # كلما زاد TDS ساءت الدرجة
    rehab_score = clip(rehab, 0, 100)                      # كما هي

    score = 0.35*aqi_score + 0.35*tds_score + 0.30*rehab_score

    # تصحيح حسب الحالة
    if status == "active":
        score += 2
    elif status == "closed":
        score -= 5

    score = clip(score, 0, 100)

    if score >= 70:
        band = "green"
    elif score >= 50:
        band = "yellow"
    else:
        band = "red"

    return score, band
