from django.urls import path
from . import views

urlpatterns = [
    path('', views.index , name='index'),
    path('bic_project', views.project, name= 'project'),
    #path('uploads/', views.serveFiles, name='serve'),
]