from django.shortcuts import render
from django.views.static import serve
from django.core.files import File
from django.contrib.gis.geos import GEOSGeometry # For lazy geometries

from .forms import DateTimeRangeForm
from .models import GPX_file, GPX_track, KML_lstring
from .utils import tracklist_to_geojson, empty_geojson, get_dtours

import datetime
import json
import time 

# TODO Revisar si estas de abajo no se si hacen falta ya
from gpx_converter import Converter
import gpxpy # For manipulating gpx files from python
import subprocess # For running bash scripts from python

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# VISTA PRINCIPAL: mapa de rutas por capas + acceso a datos #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def index(request):
    # Retrieve the GPX_file
    gpx_tracks = GPX_track.objects.all()
    kml_tracks = KML_lstring.objects.all() 
    polys = [] # lista para guardar los polys con los q hacer el ST_Diff
    
    # RETRIEVE already buffered BIDEGORRIS
    bidegorris = tracklist_to_geojson(kml_tracks, "poly")    
    
    # Llenamos la lista de bidegorris poligonizados
    for track in kml_tracks:
        polys.append(track.poly)

    # Calculamos dtours con los bidegorris = difference from track and bidegorri (mlstrings)
    dtours = get_dtours(gpx_tracks, polys)

    # RETRIEVE ALL tracks = stored GPX tracks (mlstrings)
    # gj_tracks = tracklist_to_geojson(gpx_tracks, "mlstring")
    gj_tracks = empty_geojson

    # ~| Center & Zoom from Zaratamap |~
    # -- coords bilbao en lon/lat --
    # -- [ 43.270200001993764,-2.9456500000716574] --> Cambiadas al pasarlas como parámetros --
    context = { "gj_tracks": gj_tracks,"gj_dtours": dtours, "gj_bidegorris": bidegorris,\
    'center': [-2.9456500000716574, 43.270200001993764],'zoom':13} # TODO pasar zoom y center como parámetro
    return render(request, 'index.html', context)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Vista del PROYECTO: En qué consiste? De dónde surge? Cuál es su propósito?  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TODO implementar 
def project(request):
    return render(request, 'project.html')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Vista de CONSULTA: Seleccionar los datos que quieren ser vistos #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
def consulta(request):

    # If this is a POST request then process the Form data
    # Sacamos los tracks correspondientes de la consulta 
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = DateTimeRangeForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # Obtenemos la info del formulario
            dates = form.clean_range_datetime()
            
            # Volvemos a crear el formulario para que se vean las fechas que hemos metido
            proposed_start_date = dates[0]
            proposed_end_date = dates[1]
            form = DateTimeRangeForm(initial={'since_datetime': proposed_start_date,
            'until_datetime':proposed_end_date })
            
            # dates[0] = form.cleaned_data['since_datetime']
            # dates[1] = form.cleaned_data['until_datetime']
            tracks = GPX_track.objects.filter(end_time__range=[dates[0], dates[1]])

            gj_tracks = tracklist_to_geojson(tracks,"mlstring")
            gj_dtours = empty_geojson()
            gj_bidegorris = empty_geojson()

            context = { 'form': form,\
            'gj_tracks': gj_tracks, "gj_dtours": gj_dtours, "gj_bidegorris": gj_bidegorris,\
            'center': [-2.9456500000716574, 43.270200001993764],'zoom':13} 

            return render(request, 'consulta.html', context)
    
    # Display de form y mapa vacíos 
    # If this is a GET (or any other method) create the default form.
    else:
        proposed_start_date = datetime.date.today() - datetime.timedelta(weeks=3)
        proposed_end_date = datetime.date.today()
        form = DateTimeRangeForm(initial={'since_datetime': proposed_start_date,
        'until_datetime':proposed_end_date })
        gj_vacio = empty_geojson()

    context = { 'form': form,\
    'gj_tracks': gj_vacio, "gj_dtours": gj_vacio, "gj_bidegorris": gj_vacio,\
    'center': [-2.9456500000716574, 43.270200001993764],'zoom':13 }

    return render(request, 'consulta.html', context)    