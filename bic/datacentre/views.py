from django.shortcuts import render
from django.views.static import serve
from .models import GPX_file, GPX_track, KML_file
from gpx_converter import Converter
from django.contrib.gis.geos import GEOSGeometry # For lazy geometries
import json
import time 
from django.core.files import File
import gpxpy # For manipulating gpx files from python
import subprocess # For running bash scripts from python

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# VISTA PRINCIPAL: mapa de rutas por capas + acceso a datos #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def index(request):
    # Retrieve the GPX_file
    gpx = GPX_file.objects.all()
    gpx_tracks = GPX_track.objects.all()
    kml = KML_file.objects.all()
    gpx_files = []
    kml_files = []
    geojson_files = []
    gpx_file = ""
    
    geojson_files.append("{\"type\": \"FeatureCollection\",\"features\": [") # Abrimos el GeoJSON con sus Features
    
    for f in kml:
        kml_files.append(f.kml_file)

    for track in gpx_tracks:
        # print("***TRACKS***")
        # print ('MLString de track', track.mlstring) #Sacamos el SRID y una lista de coordenadas 
        gpx_track = track.mlstring # MultiLineString 
        geojson_files.append("{\"type\": \"Feature\",\"geometry\": ") #Inicio de una Feature
        geojson_files.append(GEOSGeometry(track.mlstring, srid=4326).geojson) #Añadimos a la lista el geojson pertinente
        
        #geojson_files.append(", \"properties\": { } }") # TODO parte de Properties

        # Para crear clase MultiLineString(coordinates, opt_layout, ot_ends)
        # - coordinates (array of Coordinate or LineString geometries)
        # - flat coordinates in combination with opt_layout and opt_ends are also accepted

    geojson_files.append("}]}") # Cerramos el GeoJSON 
    geojson = ''.join(geojson_files)
    

#    print('\n\n\n\n', geojson) # Printea el GeoJSON ya formateado

    for f in gpx:
        # geojson = subprocess.call(['sh','./togeojson.sh', nomGPX]) # Esto convierte un archivo GPX a GeoJSON dejando el nuevo en la carpeta
        # geojson_files.append(geojson) 
        print (str(f.gpx_file))
        gpx_file = open(str(f.gpx_file))
        gpx = gpxpy.parse(gpx_file)
        gpx_files.append(gpx.to_xml)
        # Este print SÍ saca el contenido del gpx a consola
        # print('GPX:', gpx.to_xml())

    # TODO Conversion using an external function   
    # gpx_to_geoJSON(gpx_files)
    
    # ~| Center & Zoom from Zaratamap |~
    # -- coords bilbao en lon/lat --
    # -- [ 43.270200001993764,-2.9456500000716574] --> Cambiadas al pasarlas como parámetros --
    context = {"gpx_files": gpx_files, "kml_files":kml_files, "geojson_files": geojson, 'center': [-2.9456500000716574, 43.270200001993764], 'zoom':13}
    return render(request, 'index.html', context)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Vista del proyecto: En qué consiste? De dónde surge? Cuál es su propósito?  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TODO implementar 
def project(request):
    return render(request, 'project.html')