# geoeco/services/ai_forecast.py
import datetime
import numpy as np
from collections import defaultdict
from django.db.models import Max
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from geoeco.models import (
    Site, ProductionMetric, EnvironmentalMetric,
    ForecastProduction, ForecastEnvironment
)

# -------- إنتاج سنوي (ETS) --------
def forecast_production_for_site(site, years_ahead=3):
    hist = (ProductionMetric.objects
            .filter(site=site)
            .order_by('year')
            .values_list('year', 'quantity'))
    hist = list(hist)
    if len(hist) < 3:
        return []  # بيانات غير كافية

    years, qty = zip(*hist)
    qty = np.array(qty, dtype=float)

    # ETS بسيط: trend فقط، بدون موسمية (سنوية)
    try:
        model = ExponentialSmoothing(qty, trend='add', seasonal=None, initialization_method='estimated')
        fit = model.fit(optimized=True)
        yhat = fit.forecast(years_ahead)
    except Exception:
        # fallback: متوسط آخر 3 سنوات
        mean3 = float(np.mean(qty[-3:]))
        yhat = np.array([mean3] * years_ahead, dtype=float)

    max_year = max(years)
    results = []
    for i in range(1, years_ahead+1):
        results.append((max_year + i, float(max(0.0, yhat[i-1]))))
    return results

# -------- بيئة شهرية (خطّي بسيط) --------
def forecast_env_for_site(site, months_ahead=6):
    hist = (EnvironmentalMetric.objects
            .filter(site=site)
            .order_by('date')
            .values_list('date', 'air_quality_index', 'water_tds', 'rehabilitation_progress'))
    hist = list(hist)
    if len(hist) < 6:
        return []  # بيانات غير كافية

    dates, aqi, tds, rehab = zip(*hist)
    n = len(dates)
    x = np.arange(n, dtype=float)

    def lin_forecast(series, h):
        s = np.array(series, dtype=float)
        # ملائمة y = a + b x
        A = np.vstack([np.ones_like(x), x]).T
        try:
            coef, _, _, _ = np.linalg.lstsq(A, s, rcond=None)
            a, b = coef
            yhat = [a + b*(n+i) for i in range(1, h+1)]
        except Exception:
            yhat = [float(np.mean(s[-3:]))] * h
        return yhat

    aqi_hat  = lin_forecast(aqi,  months_ahead)
    tds_hat  = lin_forecast(tds,  months_ahead)
    reh_hat  = lin_forecast(rehab, months_ahead)

    last_date = dates[-1]
    # توليد شهور قادمة
    results = []
    for i in range(1, months_ahead+1):
        # تقدّم شهرًا
        if last_date.month + i <= 12:
            mth = last_date.month + i
            yr  = last_date.year
        else:
            mth = (last_date.month + i) % 12
            yr  = last_date.year + (last_date.month + i - 1) // 12
            if mth == 0: mth = 12
        d = datetime.date(yr, mth, 1)
        results.append((d, max(0.0, aqi_hat[i-1]), max(0.0, tds_hat[i-1]), max(0.0, reh_hat[i-1])))
    return results

def run_site_forecasts(site, years_ahead=3, months_ahead=6):
    # احذف القديم لنفس الآفاق
    ForecastProduction.objects.filter(site=site).delete()
    ForecastEnvironment.objects.filter(site=site).delete()

    for y, q in forecast_production_for_site(site, years_ahead):
        ForecastProduction.objects.create(site=site, year=y, quantity=round(q, 2))

    for d, aqi, tds, rehab in forecast_env_for_site(site, months_ahead):
        ForecastEnvironment.objects.create(
            site=site,
            date=d,
            air_quality_index=round(aqi, 1),
            water_tds=round(tds, 1),
            rehabilitation_progress=round(min(100.0, max(0.0, rehab)), 1),
        )
