from django.shortcuts import render
from django.views.static import serve
from .models import GPX_file, GPX_track, KML_lstring
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
    gpx_tracks = GPX_track.objects.all()
    kml_tracks = KML_lstring.objects.all()
    gj_bidegorris = [] # GeoJSON bidegorris = stored KML bidegorris (lstrings)
    gj_tracks = [] # GeoJSON tracks = stored GPX tracks (mlstrings)
    gj_dtours = [] # GeoJSON dtours = difference from track and bidegorri (mlstrings)
    buff_bidegorris = [] # Buffered_bidegorris (polys)

    buffers_de_prueba = []      
    
    # Abrimos los GeoJSON con sus Features
    gj_bidegorris.append("{\"type\": \"FeatureCollection\",\"features\": [")
    gj_dtours.append("{\"type\": \"FeatureCollection\",\"features\": [") 
    gj_tracks.append("{\"type\": \"FeatureCollection\",\"features\": [")
    buff_bidegorris.append("{\"type\": \"FeatureCollection\",\"features\": [")
    # Contador para pruebas
    cont=0

    # RETRIEVE already buffered BIDEGORRIS
    # for track in kml_tracks:
    #     buff_bidegorris.append("{\"type\": \"Feature\",\"geometry\": ") #Inicio de una Feature
    #     buff_bidegorris.append(GEOSGeometry(track.lstring, srid=4326).geojson) #Añadimos a la lista el geojson pertinente
    #     buff_bidegorris.append("},") # Cerramos el Feature (track) 
    #     #gj_tracks.append(", \"properties\": { } }") # TODO parte de Properties

    # if len(buff_bidegorris) > 1:
    #     buff_bidegorris = buff_bidegorris[:-1] # Quitamos la coma para el último track
    #     buff_bidegorris.append("}")

    # buff_bidegorris.append("]}") # Cerramos el GeoJSON 
    # bidegorris = ''.join(gj_tracks) #TODO cambiar nombre a esta variable a geojson_trks o algo así
    # FIN RETRIEVE buffered bidegorris    

    # ST_Buffer() --> Aquí deben ir los gj_bidegorris (esto se puede hacer solo una vez)
    for track in kml_tracks:
        buff_bidegorris.append("{\"type\": \"Feature\",\"geometry\": ")
        line = GEOSGeometry(track.lstring, srid=4326)
        buffered_line = line.buffer(0.00005,quadsegs=8) # Aquí hacemos el buffer con la distancia que queramos
        buff_bidegorris.append(buffered_line.geojson) 
        #prueba para Difference
        buffers_de_prueba.append(buffered_line) # metemos los polys correspondientes
        buff_bidegorris.append("},")
        # limitar cantidad en pruebas
    if len(buff_bidegorris) > 1:
        buff_bidegorris = buff_bidegorris[:-1] # Quitamos la coma para el último track

    buff_bidegorris.append("}]}") # Cerramos el GeoJSON 
    buffered_l = ''.join(buff_bidegorris)
    # FIN ST_Buffer()    
    
    # ST_Difference()
    for t in gpx_tracks:
        track = GEOSGeometry(t.mlstring, srid=4326)
        for i in buffers_de_prueba: # sacamos cada poly de la lista
            if track.intersects(i):# if they intersect --> then do the .difference()
                intersected = True
                track = track.difference(i) # Guardamos el resultante como nuevo track y guardamos solo al final
        if intersected:
            gj_dtours.append("{\"type\": \"Feature\",\"geometry\": ")
            dtour = track # Difference = Track - Poly
            print(dtour.geom_type)
            gj_dtours.append(dtour.geojson)
            gj_dtours.append("},")
            intersected = False
                
    cont=0
    if len(gj_dtours) > 1:
        gj_dtours = gj_dtours[:-1] # Quitamos la coma para el último track
    
    gj_dtours.append("}]}") # Cerramos el GeoJSON 
    geojson_d = ''.join(gj_dtours)
    # FIN ST_Difference()

    # STORE ALL TRACKS
    # for track in gpx_tracks:
    #     # print("***TRACKS***")
    #     # print ('MLString de track', track.mlstring) #Sacamos el SRID y una lista de coordenadas 
    #     gj_tracks.append("{\"type\": \"Feature\",\"geometry\": ") #Inicio de una Feature
    #     gj_tracks.append(GEOSGeometry(track.mlstring, srid=4326).geojson) #Añadimos a la lista el geojson pertinente
    #     gj_tracks.append("},") # Cerramos el Feature (track) 
    #     #gj_tracks.append(", \"properties\": { } }") # TODO parte de Properties
        
    #     cont+=1
    #     if cont ==3:
    #         break

    # if len(gj_tracks) > 1:
    #     gj_tracks = gj_tracks[:-1] # Quitamos la coma para el último track
    #     gj_tracks.append("}")

    gj_tracks.append("]}") # Cerramos el GeoJSON 
    geojson = ''.join(gj_tracks) #TODO cambiar nombre a esta variable a geojson_trks o algo así
    # FIN STORE ALL TRACKS

    # ~| Center & Zoom from Zaratamap |~
    # -- coords bilbao en lon/lat --
    # -- [ 43.270200001993764,-2.9456500000716574] --> Cambiadas al pasarlas como parámetros --
    context = {"gj_bidegorris":gj_bidegorris, "gj_tracks": geojson,\
    "gj_dtours": geojson_d, "buff_bidegorris": buffered_l,\
    'center': [-2.9456500000716574, 43.270200001993764],'zoom':13} # TODO pasar zoom y center com parámetro
    return render(request, 'index.html', context)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Vista del proyecto: En qué consiste? De dónde surge? Cuál es su propósito?  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# TODO implementar 
def project(request):
    return render(request, 'project.html')