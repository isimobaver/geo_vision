
from django.contrib import admin
from .models import Company, Mineral, Site, ProductionMetric, EnvironmentalMetric, License, Alert

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name","sustainability_score")

@admin.register(Mineral)
class MineralAdmin(admin.ModelAdmin):
    list_display = ("name","unit")

class ProductionInline(admin.TabularInline):
    model = ProductionMetric
    extra = 0

class EnvInline(admin.TabularInline):
    model = EnvironmentalMetric
    extra = 0

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name","company","mineral","status","sustainability_band","governorate")
    list_filter = ("status","sustainability_band","governorate","mineral")
    inlines = [ProductionInline, EnvInline]

admin.site.register(ProductionMetric)
admin.site.register(EnvironmentalMetric)
admin.site.register(License)
admin.site.register(Alert)
