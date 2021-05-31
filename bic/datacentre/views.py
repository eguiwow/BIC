from django.shortcuts import render
from django.views.static import serve
from django.core.files import File
from django.contrib.gis.geos import Point, Polygon, GEOSGeometry # For lazy geometries
from django.utils import timezone

from .forms import DateTimeRangeBBoxForm, ConfigForm, ConfigDevicesForm
from .models import GPX_file, Track, BikeLane, Measurement, Sensor, Config, SCK_device, Dtour
from .utils import tracklist_to_geojson, empty_geojson, get_dtours, get_lista_puntos, measurements_to_geojson
from .sck_api import check_devices

import datetime
import json
import time 
import math

# REST
from rest_framework import viewsets
from .serializers import TrackSerializer, BikeLaneSerializer, MeasurementSerializer, DtourSerializer

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# VISTA PRINCIPAL: mapa de rutas por capas + acceso a datos #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def datacentre(request):
    return render(request, 'datacentre.html')


def movilidad(request):
    # Retrieve config
    config = Config.objects.get(name="base_config")

    # Retrieve the tracks
    tracks = Track.objects.all()
    kml_tracks = BikeLane.objects.all() 
    dtour_tracks = Dtour.objects.all()
    
    # Retrieve config
    config = Config.objects.get(name="base_config")
    
    # RETRIEVE tracks
    gj_bidegorris = tracklist_to_geojson(kml_tracks, "bidegorris")    
    gj_tracks = tracklist_to_geojson(tracks, "tracks")
    gj_dtours = tracklist_to_geojson(dtour_tracks, "dtours")
    gj_points = tracklist_to_geojson(tracks, "points") # Puntos de los tracks para Heatmap


    # ~| Center & Zoom from Zaratamap |~
    # -- coords bilbao en lon/lat --
    # -- [ 43.270200001993764,-2.9456500000716574] --> Cambiadas al pasarlas como parámetros --
    context = { "gj_tracks": gj_tracks,"gj_dtours": gj_dtours, "gj_bidegorris": gj_bidegorris,\
    'gj_points': gj_points,\
    'center': [config.lon, config.lat],'zoom':config.zoom}
    return render(request, 'movilidad.html', context)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Vista del PROYECTO: En qué consiste? De dónde surge? Cuál es su propósito?  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
def proyecto(request):
    return render(request, 'proyecto.html')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Vista de CONFIGURACIÓN: Configurar center mapa y más  #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def config(request):
    # Retrieve config
    config = Config.objects.get(name="base_config")
    kits = config.devices.all()
    kit_ids = []
    for k in kits:
        kit_ids.append(k.sck_id)
    
    # If this is a POST request then process the Form data
    if request.method == 'POST':
        form = ConfigForm(request.POST)
        if 'center' in request.POST:        
            # Check if the form is valid:
            if form.is_valid():
                # Obtenemos la info del formulario
                
                center = form.clean_range_center()
                # Guardamos la nueva configuración
                config.lon = center[0]
                config.lat = center[1]
                config.zoom = center[2]
                config.save()

                form = ConfigForm(initial={'center_zoom': center[2],
                'center_lon':center[0],'center_lat': center[1]})
                context = { 'form': form, 'kits': kit_ids} 

                return render(request, 'config.html', context)
        
        elif 'refresh_devices' in request.POST:
            check_devices()
            form = ConfigForm(initial={'center_zoom': config.zoom,
            'center_lon':config.lon,'center_lat': config.lat})
            context = { 'form': form, 'kits': kit_ids} 

            return render(request, 'config.html', context)

        elif 'edit_list' in request.POST:
            form = ConfigDevicesForm(initial={'center_zoom': config.zoom,
            'center_lon':config.lon,'center_lat': config.lat})
            context = { 'form': form, 'kits': kit_ids} 

            return render(request, 'config_list.html', context)
    # Display de form y mapa vacíos 
    # If this is a GET (or any other method) create the default form.
    else:
        form = ConfigForm(initial={'center_zoom': config.zoom,
        'center_lon':config.lon,'center_lat': config.lat})

    context = { 'form': form, 'kits': kit_ids}

    return render(request, 'config.html', context)

def config_list(request):
    # Retrieve config
    config = Config.objects.get(name="base_config")
    kits = config.devices.all()
    kit_ids = []
    for k in kits:
        kit_ids.append(k.sck_id)
    
    # If this is a POST request then process the Form data
    if request.method == 'POST':
        form = ConfigDevicesForm(request.POST)
        if 'anyadir_device' in request.POST:        
            # Check if the form is valid:
            if form.is_valid():
                # Obtenemos la info del formulario

                new_id = form.clean_add_id(kit_ids)
                device = SCK_device(sck_id=new_id).save()
                config.devices.add(SCK_device.objects.get(sck_id=new_id))
                kit_ids.append(new_id)

                form = ConfigDevicesForm()
                context = { 'form': form, 'kits': kit_ids} 

                return render(request, 'config_list.html', context)

        elif 'eliminar_device' in request.POST:   
            if form.is_valid():
                # Obtenemos la info del formulario
                delete_id = form.clean_delete_id(kit_ids)
                config.devices.remove(SCK_device.objects.get(sck_id=delete_id))
                device = SCK_device.objects.get(sck_id=delete_id).delete()
                kit_ids.remove(delete_id)

                form = ConfigDevicesForm()
                context = { 'form': form, 'kits': kit_ids} 

                return render(request, 'config_list.html', context)

    # If this is a GET (or any other method) create the default form.
    else:
        form = ConfigDevicesForm()

    context = { 'form': form, 'kits': kit_ids}

    return render(request, 'config_list.html', context)



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Vista de CONSULTA: Seleccionar los datos que quieren ser vistos #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
def consulta(request):
    # Retrieve config
    config = Config.objects.get(name="base_config")

    # Gestionar Bidegorris    
    kml_tracks = BikeLane.objects.all()
    bidegorris = tracklist_to_geojson(kml_tracks, "bidegorris")
    consulta_vacia = 0 # para alerta por consulta vacía
    dtour_l = []
    sensor_air = Sensor.objects.get(sensor_id= 87) # Sensor PM 2.5
    sensor_noise = Sensor.objects.get(sensor_id= 53) # Sensor Noise (dBA)
    sensor_temp = Sensor.objects.get(sensor_id= 55) # Sensor Temperatura (ºC)


    # If this is a POST request then process the Form data
    # Sacamos los tracks correspondientes de la consulta 
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = DateTimeRangeBBoxForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # Obtenemos la info del formulario
            dates = form.clean_range_datetime()
            bbox_ne_lon = form.cleaned_data["NE_lon"]
            bbox_ne_lat = form.cleaned_data["NE_lat"]
            bbox_sw_lon = form.cleaned_data["SW_lon"]
            bbox_sw_lat = form.cleaned_data["SW_lat"]
            # Volvemos a crear el formulario para que se vean las fechas que hemos metido
            proposed_start_date = dates[0]
            proposed_end_date = dates[1]

            form = DateTimeRangeBBoxForm(initial={'since_datetime': proposed_start_date,
            'until_datetime':proposed_end_date, 'NE_lon': bbox_ne_lon,
             'NE_lat': bbox_ne_lat,'SW_lon': bbox_sw_lon,'SW_lat': bbox_sw_lat})
            
            # Creamos bbox partiendo de la entrada de usuario
            bbox = (bbox_sw_lon, bbox_sw_lat, bbox_ne_lon, bbox_ne_lat)
            geom = Polygon.from_bbox(bbox) # (xmin, ymin, xmax, ymax)
            new_center_lon = float((bbox_sw_lon + bbox_ne_lon) /2 )
            new_center_lat = float((bbox_sw_lat + bbox_ne_lat) /2 )
            
            dif_grados = (bbox_ne_lon - bbox_sw_lon)*10000 # diferencia en metros
            if dif_grados>50:                
                exponente = math.log((dif_grados/50),2)
                new_center_zoom = 18-exponente
            else:
                new_center_zoom = config.zoom
            # Filtro de rango de tiempo + Filtro espacial (BBox)
            # INFO: Ahora mismo, el bbox tiene que contener enteramente el track para mostrarlo (pensar si es así la mejor manera)
            tracks = Track.objects.filter(end_time__range=[dates[0], dates[1]]).filter(mlstring__contained=geom)
            for t in tracks:
                dtour_qs = Dtour.objects.filter(track=t)
                if dtour_qs:
                    for d in dtour_qs:
                        dtour_l.append(d)
            gj_dtours = tracklist_to_geojson(dtour_l, "dtours")
            gj_tracks = tracklist_to_geojson(tracks,"tracks")     

            measurements_air = Measurement.objects.filter(sensor=sensor_air).filter(time__range=[dates[0], dates[1]]).filter(point__contained=geom)
            measurements_noise = Measurement.objects.filter(sensor=sensor_noise).filter(time__range=[dates[0], dates[1]]).filter(point__contained=geom)
            measurements_temp = Measurement.objects.filter(sensor=sensor_temp).filter(time__range=[dates[0], dates[1]]).filter(point__contained=geom)
            gj_air = measurements_to_geojson(measurements_air)
            gj_noise = measurements_to_geojson(measurements_noise)
            gj_temp = measurements_to_geojson(measurements_temp)

            if not tracks:
                consulta_vacia = 1
            else:
                consulta_vacia = 0

            context = { 'form': form, 'consulta_vacia': consulta_vacia,\
            'gj_tracks': gj_tracks, "gj_dtours": gj_dtours, "gj_bidegorris": bidegorris,\
            "gj_air": gj_air,"gj_noise": gj_noise, "gj_temp": gj_temp,\
            'center': [new_center_lon, new_center_lat],'zoom':new_center_zoom} 

            return render(request, 'consulta.html', context)
    

    # Display de form y mapa vacíos 
    # If this is a GET (or any other method) create the default form.
    else:
        proposed_start_date = datetime.date.today() - datetime.timedelta(weeks=52)
        proposed_end_date = timezone.now()
        proposed_sw = Point(-3, 40)
        proposed_ne = Point(-1, 44)
        form = DateTimeRangeBBoxForm(initial={'since_datetime': proposed_start_date,
        'until_datetime':proposed_end_date,'NE_lon': proposed_ne[0],
        'NE_lat': proposed_ne[1],'SW_lon': proposed_sw[0],'SW_lat': proposed_sw[1]})

    gj_vacio = empty_geojson()
    context = { 'form': form,\
    'gj_tracks': gj_vacio, "gj_dtours": gj_vacio, "gj_bidegorris": gj_vacio,\
    "gj_air": gj_vacio,"gj_noise": gj_vacio, "gj_temp": gj_vacio,\
    'center': [config.lon, config.lat],'zoom':config.zoom}  

    return render(request, 'consulta.html', context)    


# # # # # # # # # # # # # # # # # # # # # #
# Vista de PRUEBAS: FUTURA VISTA ANÁLISIS #
# # # # # # # # # # # # # # # # # # # # # # 
def analisis(request):
    # Retrieve config
    config = Config.objects.get(name="base_config")

    tracks = Track.objects.all()        
    kml_tracks = BikeLane.objects.all()
    dtour_tracks = Dtour.objects.all()
 
    bidegorris = tracklist_to_geojson(kml_tracks, "bidegorris") # Buffered Bidegorris   
    gj_tracks = tracklist_to_geojson(tracks, "tracks")
    gj_dtours = tracklist_to_geojson(dtour_tracks, "dtours")
    
    # Parte de get datos cont. acústica y atmosférica
    sensor_air = Sensor.objects.get(sensor_id= 87) # Sensor PM 2.5
    sensor_noise = Sensor.objects.get(name= "ICS43432 - Noise") # Sensor Noise (dBA)
    sensor_temp = Sensor.objects.get(name= "SHT31 - Temperature") # Sensor Temperatura (ºC)
    measurements_air = Measurement.objects.filter(sensor=sensor_air)
    measurements_noise = Measurement.objects.filter(sensor=sensor_noise)
    measurements_temp = Measurement.objects.filter(sensor=sensor_temp)
    
    gj_air = measurements_to_geojson(measurements_air)
    gj_noise = measurements_to_geojson(measurements_noise)
    gj_temp = measurements_to_geojson(measurements_temp)

    
    context = { "gj_tracks": gj_tracks,"gj_dtours": gj_dtours, "gj_bidegorris": bidegorris,\
    "gj_air": gj_air,"gj_noise": gj_noise, "gj_temp": gj_temp,\
    'center': [config.lon, config.lat],'zoom':config.zoom}

    return render(request, 'analisis.html', context)





# # # # # # # # # #
# REST FRAMEWORK  #
# # # # # # # # # #
class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all().order_by('end_time')
    serializer_class = TrackSerializer  

class BikeLaneViewSet(viewsets.ModelViewSet):
    queryset = BikeLane.objects.all().order_by('distance')
    serializer_class = BikeLaneSerializer 

class MeasurementViewSet(viewsets.ModelViewSet):
    queryset = Measurement.objects.all().order_by('time')
    serializer_class = MeasurementSerializer 

class DtourViewSet(viewsets.ModelViewSet):
    queryset = Dtour.objects.all().order_by('distance')
    serializer_class = DtourSerializer 

