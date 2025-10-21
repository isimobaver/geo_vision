from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from geoeco.geo.oman_polygon import point_in_oman

OMAN_BOUNDS = {
    "min_lat": 16.5, "max_lat": 26.6,
    "min_lon": 51.8, "max_lon": 60.5,
}

class Company(models.Model):
    name = models.CharField(max_length=200)
    sustainability_score = models.FloatField(default=0)
    def __str__(self): return self.name

class Mineral(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, default="ton")
    def __str__(self): return self.name

class Site(models.Model):
    name = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    mineral = models.ForeignKey(Mineral, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=[("active","نشط"),("proposed","مقترح"),("closed","منتهي")], default="proposed")
    sustainability_band = models.CharField(max_length=10, choices=[("green","أخضر"),("yellow","أصفر"),("red","أحمر")], default="yellow")
    lat = models.FloatField(validators=[MinValueValidator(OMAN_BOUNDS["min_lat"]), MaxValueValidator(OMAN_BOUNDS["max_lat"])])
    lon = models.FloatField(validators=[MinValueValidator(OMAN_BOUNDS["min_lon"]), MaxValueValidator(OMAN_BOUNDS["max_lon"])])
    governorate = models.CharField(max_length=100, default="")
    def __str__(self): return self.name

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(lat__gte=OMAN_BOUNDS["min_lat"]) &
                    models.Q(lat__lte=OMAN_BOUNDS["max_lat"]) &
                    models.Q(lon__gte=OMAN_BOUNDS["min_lon"]) &
                    models.Q(lon__lte=OMAN_BOUNDS["max_lon"])
                ),
                name="chk_site_in_oman_bounds",
            )
        ]
    def clean(self):
        if self.lat is None or self.lon is None:
            raise ValidationError("يجب توفير إحداثيات lat/lon.")
        if not point_in_oman(self.lat, self.lon):
            raise ValidationError("الإحداثيات ليست داخل الحدود البرية لسلطنة عمان.")

class ProductionMetric(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="production")
    year = models.IntegerField()
    quantity = models.FloatField()
    class Meta:
        unique_together = ("site","year")

class EnvironmentalMetric(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="env")
    date = models.DateField()
    air_quality_index = models.FloatField(null=True, blank=True)
    water_tds = models.FloatField(null=True, blank=True)
    rehabilitation_progress = models.FloatField(default=0)

class License(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="licenses")
    license_no = models.CharField(max_length=100)
    issued_on = models.DateField()
    expires_on = models.DateField()

class Alert(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="alerts")
    created_at = models.DateTimeField(default=timezone.now)  # افتراضي لتفادي مشاكل fixtures
    level = models.CharField(max_length=10, choices=[("info","Info"),("warn","Warn"),("critical","Critical")], default="info")
    message = models.TextField()

class ForecastProduction(models.Model):
    site = models.ForeignKey('Site', on_delete=models.CASCADE, related_name='prod_forecasts')
    year = models.IntegerField()
    quantity = models.FloatField()  # نفس وحدة إنتاج الموقع (طن أو كغ للذهب)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('site', 'year')

class ForecastEnvironment(models.Model):
    site = models.ForeignKey('Site', on_delete=models.CASCADE, related_name='env_forecasts')
    date = models.DateField()  # تاريخ شهري متوقع
    air_quality_index = models.FloatField()
    water_tds = models.FloatField()
    rehabilitation_progress = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('site', 'date')
