
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from pathlib import Path

class Command(BaseCommand):
    help = "Load demo dataset for GeoEco Tracker"

    def handle(self, *args, **options):
        seed_path = Path(settings.BASE_DIR) / 'seed.json'
        self.stdout.write(self.style.WARNING(f"Loading seed from {seed_path}..."))
        call_command('loaddata', str(seed_path))
        self.stdout.write(self.style.SUCCESS("Demo data loaded."))
