from django.shortcuts import render
from django.views.static import serve
from .models import GPX_file, KML_file
from gpx_converter import Converter
from .utils import parse_gpx_file
import json
import time
from django.core.files import File
import gpxpy
import subprocess
# Library for bonding js interpreter to python to execute a gpx -> geojson conversion
# import bond


# Vista principal: mapa de rutas por capas + acceso a datos
# TODO pasar los GPX como Features de un GeoJSON

def index(request):
    gpx = GPX_file.objects.all()
    kml = KML_file.objects.all()
    gpx_files = []
    gpx_file = ""
    geojson_files = []
    kml_files = []
    
    for f in kml:
        kml_files.append(f.kml_file)

    for f in gpx:
        # geojson = subprocess.call(['sh','./togeojson.sh', nomGPX]) # Esto convierte un archivo GPX a GeoJSON dejando el nuevo en la carpeta
        # geojson_files.append(geojson) 
        print (str(f.gpx_file))
        gpx_file = open(str(f.gpx_file))
        gpx = gpxpy.parse(gpx_file)
        gpx_files.append(gpx.to_xml)
        # Este print SÍ saca el contenido del gpx a consola
        # print('GPX:', gpx.to_xml())
        # Llamada a función JS del archivo togeojson.js a través de un intérprete Node.js
        # geojson_files.append(python.call('toGeoJSON', gpx_file))

    # Conversion using an external function (not yet implemented)     
    # gpx_to_geoJSON(gpx_files)
    
    # Center & Zoom from Zaratamap
    # -- coords bilbao en lon/lat
    # [ 43.270200001993764,-2.9456500000716574] --> Cambiadas al pasarlas como parámetros
    context = {"gpx_files": gpx_files, "kml_files":kml_files, "geojson_files": geojson_files, 'center': [-2.9456500000716574, 43.270200001993764], 'zoom':13}
    return render(request, 'index.html', context)

# Vista del proyecto: En qué consiste? De dónde surge? Cuál es su propósito?
# TODO implementar 

def project(request):
    return render(request, 'project.html')