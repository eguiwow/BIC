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
    geojson_tracks = []
    geojson_dtours = []

    gpx_file = ""
      
    for f in kml:
        kml_files.append(f.kml_file)

    geojson_dtours.append("{\"type\": \"FeatureCollection\",\"features\": [") # Abrimos el GeoJSON con sus Features
    geojson_tracks.append("{\"type\": \"FeatureCollection\",\"features\": [") # Abrimos el GeoJSON con sus Features

    # RAW SQL probando
    for t in GPX_track.objects.raw( # Ejecutamos el query que debe hacer la diferencia de los tracks
        '''SELECT p1.id ,p2.id, ST_AsText(
        ST_Difference(p1.mlstring,p2.mlstring)
        ) AS diff_geom
        FROM datacentre_gpx_track AS p1, datacentre_gpx_track AS p2 WHERE p1.id > p2.id;'''):
        geojson_dtours.append("{\"type\": \"Feature\",\"geometry\": ")
        geojson_dtours.append(GEOSGeometry(t.mlstring, srid=4326).geojson)
        geojson_dtours.append("},")

    if len(geojson_dtours) > 1:
        geojson_dtours = geojson_dtours[:-1] # Quitamos la coma para el último track

    geojson_dtours.append("}]}") # Cerramos el GeoJSON 
    geojson_d = ''.join(geojson_dtours)
    
    for track in gpx_tracks:
        # print("***TRACKS***")
        # print ('MLString de track', track.mlstring) #Sacamos el SRID y una lista de coordenadas 
        geojson_tracks.append("{\"type\": \"Feature\",\"geometry\": ") #Inicio de una Feature
        geojson_tracks.append(GEOSGeometry(track.mlstring, srid=4326).geojson) #Añadimos a la lista el geojson pertinente
        geojson_tracks.append("},") # Cerramos el Feature (track) 
        #geojson_tracks.append(", \"properties\": { } }") # TODO parte de Properties

        # Para crear clase MultiLineString(coordinates, opt_layout, ot_ends)
        # - coordinates (array of Coordinate or LineString geometries)
        # - flat coordinates in combination with opt_layout and opt_ends are also accepted 
    if len(geojson_tracks) > 1:
        geojson_tracks = geojson_tracks[:-1] # Quitamos la coma para el último track

    geojson_tracks.append("}]}") # Cerramos el GeoJSON 
    geojson = ''.join(geojson_tracks) #TODO cambiar nombre a esta variable a geojson_trks o algo así

#    print('\n\n\n\n', geojson) # Printea el GeoJSON ya formateado

    for f in gpx:
        # geojson = subprocess.call(['sh','./togeojson.sh', nomGPX]) # Esto convierte un archivo GPX a GeoJSON dejando el nuevo en la carpeta
        # geojson_tracks.append(geojson) 
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
    context = {"gpx_files": gpx_files, "kml_files":kml_files, "geojson_tracks": geojson, "geojson_dtours": geojson_d, 'center': [-2.9456500000716574, 43.270200001993764], 'zoom':13}
    return render(request, 'index.html', context)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Vista del proyecto: En qué consiste? De dónde surge? Cuál es su propósito?  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TODO implementar 
def project(request):
    return render(request, 'project.html')