
from django.contrib import admin
from django.urls import path
from geoeco import views
from geoeco.views import api_site_forecast

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('map/', views.map_view, name='map'),
    path('site/<int:site_id>/', views.site_detail, name='site_detail'),
    path('investors/', views.investors, name='investors'),
    path('search/', views.search_view, name='search'),
    path('forecast/site/<int:site_id>/', api_site_forecast, name='api_site_forecast'),
    
]
