from django.shortcuts import render
from django.views.static import serve
from .models import GPX_file, KML_file
from gpx_converter import Converter
import json
import time

def index(request):
    gpx = GPX_file.objects.all()
    kml = KML_file.objects.all()
    gpx_files = []
    json_files = []
    paths = ""
    kml_file = ""

    # For de prueba para ver si pinta kml únicamente con url
    for f in kml:
        kml_file = f.kml_file.path

    for f in gpx:
        gpx_files.append(f.gpx_file) #Pasamos el path
        paths += f.gpx_file.path + "#"
        json_name = f.gpx_name + ".json"
        json_files.append(Converter(input_file=f.gpx_file.path).gpx_to_json(output_file=json_name))
        print(f.gpx_name)
    
    
    # for f in json_files:
    #     with open(f) as jsonFile:
    #         time.sleep(1000)
    #         print("before loading")
    #         data = json.load(jsonFile)
    #         print("AJJAAJJ")
    #         print(data)
    # # Center & Zoom from Zaratamap
    

    # coords bilbao en lon/lat
    #context = {"gpx_files": gpx_files, 'center': [ 43.270200001993764,-2.9456500000716574], 'zoom':14}
    # coords en metros (mercator) CONSEGUIR cambiar de proyección
    context = {"gpx_files": gpx_files, "kml_files":kml_file,  'paths': paths, 'center': [-2.9456500000716574, 43.270200001993764], 'zoom':13}
    return render(request, 'index.html', context)


def serveFiles(request):
    filepath = request.get_full_path()
    return serve(request, os.path.basename(filepath), os.path.dirname(filepath))
