from django.urls import path
from . import views

urlpatterns = [
    path('datacentre', views.index , name='index'),
    path('bic_project', views.project, name= 'project'),
    path('query', views.consulta, name= 'consulta'),
]