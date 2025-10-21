# geoeco/management/commands/update_forecasts.py
from django.core.management.base import BaseCommand
from geoeco.models import Site
from geoeco.services.ai_forecast import run_site_forecasts
from geoeco.services.band_logic import band_from_env
from geoeco.models import EnvironmentalMetric

class BaseBandException(Exception):
    pass

class Command(BaseCommand):
    help = "Update AI forecasts (production & environment) and recalc sustainability band."

    def add_arguments(self, parser):
        parser.add_argument("--years_ahead", type=int, default=3)
        parser.add_argument("--months_ahead", type=int, default=6)
        parser.add_argument("--recalc_band", action="store_true", help="Recalculate band from latest env metrics")

    def handle(self, *args, **o):
        years_ahead = o["years_ahead"]
        months_ahead = o["months_ahead"]
        recalc_band = o["recalc_band"]

        sites = Site.objects.all()
        for s in sites:
            run_site_forecasts(s, years_ahead=years_ahead, months_ahead=months_ahead)

            if recalc_band:
                latest = (EnvironmentalMetric.objects
                          .filter(site=s)
                          .order_by('-date')
                          .values('air_quality_index','water_tds','rehabilitation_progress')
                          .first())
                if latest:
                    score, band = band_from_env(
                        latest["air_quality_index"],
                        latest["water_tds"],
                        latest["rehabilitation_progress"],
                        s.status
                    )
                    if s.sustainability_band != band:
                        s.sustainability_band = band
                        s.save(update_fields=["sustainability_band"])

        self.stdout.write(self.style.SUCCESS("Forecasts updated ✅"))
