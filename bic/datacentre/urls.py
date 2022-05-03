from django.urls import path, include
from . import views
from rest_framework import routers
# API routing
# https://medium.com/swlh/build-your-first-rest-api-with-django-rest-framework-e394e39a482c 
router = routers.DefaultRouter()
router.register(r'tracks', views.TrackViewSet)
router.register(r'bikelanes', views.BikeLaneViewSet)
router.register(r'measurements', views.MeasurementViewSet)
router.register(r'dtours', views.DtourViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('datacentre', views.datacentre , name='datacentre'),
    path('recent', views.recent , name='recent'),
    path('movilidad', views.movilidad , name='movilidad'),
    path('bic_proyecto', views.proyecto, name= 'proyecto'),
    path('consulta', views.consulta, name= 'consulta'),
    path('analisis', views.analisis, name= 'analisis'),
    path('config', views.config, name= 'config'),
    path('config-list', views.config_list, name= 'config_list'),
    # API
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]