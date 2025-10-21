
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Avg
from .models import Site, Company, Mineral, ProductionMetric, EnvironmentalMetric, Alert,ForecastProduction, ForecastEnvironment
from django.http import JsonResponse, Http404
def home(request):
    # Login/landing page (static for prototype)
    kpis = {
        "sites": Site.objects.count(),
        "sustainable_projects": Site.objects.filter(sustainability_band="green").count(),
    }
    return render(request, "geoeco/home.html", {"kpis": kpis})

def dashboard(request):
    total_sites = Site.objects.count()
    green = Site.objects.filter(sustainability_band="green").count()
    yellow = Site.objects.filter(sustainability_band="yellow").count()
    red = Site.objects.filter(sustainability_band="red").count()

    # production by mineral (sum latest year)
    latest_year = ProductionMetric.objects.order_by("-year").values_list("year", flat=True).first()
    prod_by_mineral = (
        ProductionMetric.objects.filter(year=latest_year)
        .values("site__mineral__name")
        .annotate(total=Sum("quantity"))
        .order_by("-total")
    )

    company_scores = Company.objects.all().values("name","sustainability_score")

    alerts = Alert.objects.order_by("-created_at")[:5]

    return render(
        request,
        "geoeco/dashboard.html",
        {
            "total_sites": total_sites,
            "green": green,
            "yellow": yellow,
            "red": red,
            "latest_year": latest_year,
            "prod_by_mineral": list(prod_by_mineral),
            "company_scores": list(company_scores),
            "alerts": alerts,
        },
    )
def map_view(request):
    # أعِدّ بيانات نظيفة للواجهة
    qs = (
        Site.objects.select_related("mineral", "company")
        .values(
            "id", "name", "lat", "lon",
            "sustainability_band", "status",
            "mineral__name", "company__name"
        )
    )
    sites_data = list(qs)
    return render(request, "geoeco/map.html", {"sites_data": sites_data})

from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Avg
from .models import Site, Company, Mineral, ProductionMetric, EnvironmentalMetric, Alert

def site_detail(request, site_id):
    site = get_object_or_404(Site, pk=site_id)

    # إنتاج سنوي: قائمة قواميس year, quantity
    production_qs = site.production.order_by("year").values("year", "quantity")
    prod_data = list(production_qs)

    # آخر 12 قراءة بيئية: حوّل التاريخ إلى نص ISO لتعمل مع JSON/Chart.js
    env_qs = site.env.order_by("-date").values("date", "air_quality_index", "water_tds", "rehabilitation_progress")[:12]
    env_data = [
        {
            "date": e["date"].isoformat(),
            "air_quality_index": e["air_quality_index"],
            "water_tds": e["water_tds"],
            "rehabilitation_progress": e["rehabilitation_progress"],
        }
        for e in env_qs
    ]
    # اعرضها زمنياً من الأقدم إلى الأحدث
    env_data = list(reversed(env_data))

    alerts = site.alerts.order_by("-created_at")[:10]

    return render(
        request,
        "geoeco/site_detail.html",
        {
            "site": site,
            "prod_data": prod_data,
            "env_data": env_data,
            "alerts": alerts,
        },
    )

def investors(request):
    # Simple list sorted by sustainability & last production
    latest_year = ProductionMetric.objects.order_by("-year").values_list("year", flat=True).first()
    rows = (
        ProductionMetric.objects.filter(year=latest_year)
        .select_related("site","site__company","site__mineral")
        .order_by("-quantity")
    )
    return render(request, "geoeco/investors.html", {"rows": rows, "latest_year": latest_year})

def search_view(request):
    q = request.GET.get("q","").strip()
    status = request.GET.get("status","")
    band = request.GET.get("band","")
    mineral = request.GET.get("mineral","")

    qs = Site.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    if status:
        qs = qs.filter(status=status)
    if band:
        qs = qs.filter(sustainability_band=band)
    if mineral:
        qs = qs.filter(mineral__name__iexact=mineral)

    minerals = Mineral.objects.values_list("name", flat=True).order_by("name")
    return render(request, "geoeco/search.html", {"sites": qs[:200], "q": q, "status": status, "band": band, "mineral": mineral, "minerals": minerals})



def api_site_forecast(request, site_id):
    try:
        s = Site.objects.get(pk=site_id)
    except Site.DoesNotExist:
        raise Http404("Site not found")

    prod = list(ForecastProduction.objects.filter(site=s).order_by('year')
                .values('year','quantity'))
    env  = list(ForecastEnvironment.objects.filter(site=s).order_by('date')
                .values('date','air_quality_index','water_tds','rehabilitation_progress'))

    return JsonResponse({"site": s.id, "production": prod, "environment": env}, safe=False)

