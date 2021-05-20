from django.urls import path, include
from . import views
from rest_framework import routers
# API routing
# https://medium.com/swlh/build-your-first-rest-api-with-django-rest-framework-e394e39a482c 
router = routers.DefaultRouter()
router.register(r'gpx_tracks', views.GPX_trackViewSet)
router.register(r'kml_tracks', views.KML_lstringViewSet)
router.register(r'measurements', views.MeasurementViewSet)

urlpatterns = [
    path('datacentre', views.index , name='index'),
    path('bic_project', views.project, name= 'project'),
    path('query', views.consulta, name= 'consulta'),
    path('analisis', views.analisis, name= 'analisis'),
    path('config', views.config, name= 'config'),
    path('config-list', views.config_list, name= 'config_list'),
    # Wire up our API using automatic URL routing.
    # Additionally, we include login URLs for the browsable API.
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]