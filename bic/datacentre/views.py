from django.shortcuts import render, redirect, reverse
from django.views.static import serve
from django.core.files import File
from django.contrib.gis.geos import Point, Polygon, GEOSGeometry # For lazy geometries
from django.utils import timezone
from django.http import JsonResponse
from numpy import empty
from .forms import DateTimeRangeBBoxForm, ConfigForm, ConfigDevicesForm, MultipleDateTimeRangeForm, UploadGPXForm, ConfigDatesForm
from .models import GPX_file, Track, BikeLane, Measurement, Sensor, Config, SCK_device, Dtour, Trackpoint
from .utils import points_vel_to_geojson, tracklist_to_geojson, empty_geojson, get_dtours, get_lista_puntos, measurements_to_geojson
from .sck_api import check_devices, calc_new_track
from .load_layers import load_gpx_from_file
# REST
from rest_framework import viewsets
from .serializers import TrackSerializer, BikeLaneSerializer, MeasurementSerializer, DtourSerializer
import datetime
import json
import time 
import math
import logging

logger = logging.getLogger(__name__)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# VISTA PRINCIPAL: mapa de rutas por capas + acceso a datos #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def datacentre(request):
    return render(request, 'datacentre.html')

def home(request):
    return redirect(reverse('datacentre'))


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# VISTA RECIENTE: última actividad registrada               #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def recent(request):
    # Retrieve config
    config = Config.objects.get(name="base_config") 

    # Retrieve the tracks - last 10 
    # https://stackoverflow.com/questions/20555673/django-query-get-last-n-records
    # -end_time significa que ordenamos inversamente 
    tracks = Track.objects.filter().order_by('-end_time')[:10]
    dtour_tracks = Dtour.objects.filter(track__in=tracks) 
    kml_tracks = BikeLane.objects.all()
    trackpoints = Trackpoint.objects.filter(track__in=tracks)
    
    km_recorridos = 0
    count = 0
    start_time = tracks[len(tracks)-1].start_time
    end_time = tracks[0].end_time
    for track in tracks:
        km_recorridos += track.distance
        count += 1
    km_recorridos = round(km_recorridos/1000)
    gj_bidegorris = tracklist_to_geojson(kml_tracks, "bidegorris")
    gj_tracks = tracklist_to_geojson(tracks, "tracks")
    gj_dtours = tracklist_to_geojson(dtour_tracks, "dtours")
    gj_points = tracklist_to_geojson(tracks, "points") # Puntos de los tracks para Heatmap
    gj_dpoints = tracklist_to_geojson(dtour_tracks, "points") # Puntos de los dtours para Heatmap
    
    # Parte de get datos cont. acústica y atmosférica
    sensor_air = Sensor.objects.get(sensor_id= 87) # Sensor PM 2.5
    sensor_noise = Sensor.objects.get(name= "ICS43432 - Noise") # Sensor Noise (dBA)
    sensor_temp = Sensor.objects.get(name= "SHT31 - Temperature") # Sensor Temperatura (ºC)
    sensor_hum = Sensor.objects.get(name= "SHT31 - Humidity") # Sensor Humedad ()
    measurements_air = Measurement.objects.filter(sensor=sensor_air).filter(trkpoint__in=trackpoints)
    measurements_noise = Measurement.objects.filter(sensor=sensor_noise).filter(trkpoint__in=trackpoints)
    measurements_temp = Measurement.objects.filter(sensor=sensor_temp).filter(trkpoint__in=trackpoints)
    measurements_hum = Measurement.objects.filter(sensor=sensor_hum).filter(trkpoint__in=trackpoints)
    num_medidas = Measurement.objects.filter(sensor=sensor_air).filter(trkpoint__in=trackpoints).count() + \
    Measurement.objects.filter(sensor=sensor_noise).filter(trkpoint__in=trackpoints).count() + \
    Measurement.objects.filter(sensor=sensor_temp).filter(trkpoint__in=trackpoints).count() + \
    Measurement.objects.filter(sensor=sensor_hum).filter(trkpoint__in=trackpoints).count()

    gj_air = measurements_to_geojson(measurements_air)
    gj_noise = measurements_to_geojson(measurements_noise)
    gj_temp = measurements_to_geojson(measurements_temp)
    gj_hum = measurements_to_geojson(measurements_hum)
    gj_vel = points_vel_to_geojson(trackpoints)
    
    if request.method == 'POST':
        if 'upload_gpx' in request.POST:
            form = UploadGPXForm(request.POST, request.FILES)
            if form.is_valid():
                
                if load_gpx_from_file(request.FILES['file']): # subimos el archivo GPX
                    archivo_ok = 1
                    # sacamos los datos con archivo GPX ya incluido 
                    tracks = Track.objects.all()
                    dtour_tracks = Dtour.objects.all()
                    trackpoints = Trackpoint.objects.filter(track__in=tracks)
                    gj_tracks = tracklist_to_geojson(tracks, "tracks")
                    gj_dtours = tracklist_to_geojson(dtour_tracks, "dtours")
                    gj_points = tracklist_to_geojson(tracks, "points") # Puntos de los tracks para Heatmap
                    gj_dpoints = tracklist_to_geojson(dtour_tracks, "points") # Puntos de los dtours para Heatmap
                    gj_vel = points_vel_to_geojson(trackpoints)
                else:
                    archivo_ok = 0
                    
                form = UploadGPXForm()
                context = { "gj_tracks": gj_tracks,"gj_dtours": gj_dtours, "gj_bidegorris": gj_bidegorris,\
                'gj_points': gj_points, 'gj_dpoints': gj_dpoints,\
                "gj_air": gj_air,"gj_noise": gj_noise, "gj_temp": gj_temp, "gj_hum": gj_hum, "gj_vel": gj_vel,\
                "km_recorridos": km_recorridos, 'start_time': start_time, 'end_time': end_time, 'num_tracks': count,'num_medidas': num_medidas,\
                'center': [config.lon, config.lat],'zoom':config.zoom, 'form':form, 'archivo_ok': archivo_ok}
                return render(request, 'reciente.html', context)
    else:
        form = UploadGPXForm()
        archivo_ok = 1 # para alerta por archivo no válido

    context = { "gj_tracks": gj_tracks,"gj_dtours": gj_dtours, "gj_bidegorris": gj_bidegorris,\
    'gj_points': gj_points, 'gj_dpoints': gj_dpoints,\
    "gj_air": gj_air,"gj_noise": gj_noise, "gj_temp": gj_temp, "gj_hum": gj_hum, "gj_vel": gj_vel,\
    "km_recorridos": km_recorridos, 'start_time': start_time, 'end_time': end_time, 'num_tracks': count,'num_medidas': num_medidas,\
    'center': [config.lon, config.lat],'zoom':config.zoom, 'form':form, 'archivo_ok': archivo_ok}

    return render(request, 'reciente.html', context)

# # # # # # # # # # # # # # # # # # # # # # # # # 
# Vista de MOVILIDAD: desvíos, velocidad, rutas #
# # # # # # # # # # # # # # # # # # # # # # # # #
def movilidad(request):
    # Retrieve config
    config = Config.objects.get(name="base_config") 

    # Gestionar Bidegorris    
    kml_tracks = BikeLane.objects.all()
    bidegorris = tracklist_to_geojson(kml_tracks, "bidegorris")
    consulta_vacia = consulta_invalida = 0 # para alerta por consulta vacía
    dtour_l = []

    # If this is a POST request then process the Form data
    # Sacamos los tracks correspondientes de la consulta 
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = DateTimeRangeBBoxForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # Obtenemos la info del formulario
            try:
                dates = form.clean_range_datetime()
            except:
                consulta_invalida = 1
            if (not consulta_invalida):
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
                tracks_api = Track.objects.filter(end_time__range=[dates[0], dates[1]]).filter(mlstring__contained=geom)
                tracks_device = Track.objects.filter(end_time__range=[dates[0], dates[1]]).filter(lstring__contained=geom)
                tracks = tracks_api.union(tracks_device)
                for t in tracks:
                    dtour_qs = Dtour.objects.filter(track=t)
                    if dtour_qs:
                        for d in dtour_qs:
                            dtour_l.append(d)
                gj_tracks = tracklist_to_geojson(tracks,"tracks")  
                gj_dtours = tracklist_to_geojson(dtour_l, "dtours")
                gj_points = tracklist_to_geojson(tracks, "points") # Puntos de los tracks para Heatmap
                gj_dpoints = tracklist_to_geojson(dtour_l, "points") # Puntos de los dtours para Heatmap   

                if not tracks:
                    gj_vel = empty_geojson()
                    consulta_vacia = 1
                else:
                    consulta_vacia = 0
                    trackpoints_1 = Trackpoint.objects.filter(track__in=tracks_api)
                    trackpoints_2 = Trackpoint.objects.filter(track__in=tracks_device)    
                    trackpoints = trackpoints_1.union(trackpoints_2)
                    gj_vel = points_vel_to_geojson(trackpoints)
            else:                
                gj_tracks = gj_dtours = gj_bidegorris = gj_points = gj_dpoints = gj_vel = empty_geojson()
                new_center_lon = config.lon
                new_center_lat = config.lat
                new_center_zoom = config.zoom
                proposed_start_date = datetime.date.today() - datetime.timedelta(weeks=52)
                proposed_end_date = timezone.now()
                proposed_sw = Point(-3, 40)
                proposed_ne = Point(-1, 44)
                form = DateTimeRangeBBoxForm(initial={'since_datetime': proposed_start_date,
                'until_datetime':proposed_end_date,'NE_lon': proposed_ne[0],
                'NE_lat': proposed_ne[1],'SW_lon': proposed_sw[0],'SW_lat': proposed_sw[1]})

            context = { 'form': form, 'consulta_vacia': consulta_vacia,\
            'gj_tracks': gj_tracks, "gj_dtours": gj_dtours, "gj_bidegorris": bidegorris,\
            'gj_points': gj_points, 'gj_dpoints': gj_dpoints, "gj_vel": gj_vel,\
            'center': [new_center_lon, new_center_lat],'zoom':new_center_zoom} 

            return render(request, 'movilidad.html', context)
    
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
    context = { 'form': form, 'consulta_vacia': consulta_vacia,\
    'gj_tracks': gj_vacio, "gj_dtours": gj_vacio, "gj_bidegorris": gj_vacio,\
    'gj_points': gj_vacio, 'gj_dpoints': gj_vacio, "gj_vel": gj_vacio,\
    'center': [config.lon, config.lat],'zoom':config.zoom} 

    return render(request, 'movilidad.html', context)    

    
# # # # # # # # # # # # # # # # # # # # # #
# Vista de ANALÍTICA: medidas sensórica   #
# # # # # # # # # # # # # # # # # # # # # # 
def analisis(request):
    # Retrieve config
    config = Config.objects.get(name="base_config")

    kml_tracks = BikeLane.objects.all()
    bidegorris = tracklist_to_geojson(kml_tracks, "bidegorris") # Buffered Bidegorris   
    consulta_vacia = consulta_invalida = 0 # para alerta por consulta vacía
    dtour_l = []     
    
    # Parte de get datos cont. acústica y atmosférica
    sensor_air = Sensor.objects.get(sensor_id= 87) # Sensor PM 2.5
    sensor_noise = Sensor.objects.get(name= "ICS43432 - Noise") # Sensor Noise (dBA)
    sensor_temp = Sensor.objects.get(name= "SHT31 - Temperature") # Sensor Temperatura (ºC)
    sensor_hum = Sensor.objects.get(name= "SHT31 - Humidity") # Sensor Humedad ()

    # If this is a POST request then process the Form data
    # Sacamos los tracks correspondientes de la consulta 
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = DateTimeRangeBBoxForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # Obtenemos la info del formulario
            try:
                dates = form.clean_range_datetime()
            except:
                consulta_invalida = 1
            if (not consulta_invalida):
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
                tracks_api = Track.objects.filter(end_time__range=[dates[0], dates[1]]).filter(mlstring__contained=geom)
                tracks_device = Track.objects.filter(end_time__range=[dates[0], dates[1]]).filter(lstring__contained=geom)
                tracks = tracks_api.union(tracks_device)
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
                measurements_hum = Measurement.objects.filter(sensor=sensor_hum).filter(time__range=[dates[0], dates[1]]).filter(point__contained=geom)

                gj_air = measurements_to_geojson(measurements_air)
                gj_noise = measurements_to_geojson(measurements_noise)
                gj_temp = measurements_to_geojson(measurements_temp)
                gj_hum = measurements_to_geojson(measurements_hum)

                if not tracks:
                    gj_vel = empty_geojson()
                    consulta_vacia = 1
                else:
                    trackpoints_1 = Trackpoint.objects.filter(track__in=tracks_api)
                    trackpoints_2 = Trackpoint.objects.filter(track__in=tracks_device)    
                    trackpoints = trackpoints_1.union(trackpoints_2)
                    gj_vel = points_vel_to_geojson(trackpoints)
                    consulta_vacia = 0
            else:
                gj_tracks = gj_dtours = gj_air = gj_noise = gj_temp = gj_hum = gj_vel = empty_geojson()
                new_center_lon = config.lon
                new_center_lat = config.lat
                new_center_zoom = config.zoom
                proposed_start_date = datetime.date.today() - datetime.timedelta(weeks=52)
                proposed_end_date = timezone.now()
                proposed_sw = Point(-3, 40)
                proposed_ne = Point(-1, 44)
                form = DateTimeRangeBBoxForm(initial={'since_datetime': proposed_start_date,
                'until_datetime':proposed_end_date,'NE_lon': proposed_ne[0],
                'NE_lat': proposed_ne[1],'SW_lon': proposed_sw[0],'SW_lat': proposed_sw[1]})

            context = { 'form': form, 'consulta_vacia': consulta_vacia,\
            'gj_tracks': gj_tracks, "gj_dtours": gj_dtours, "gj_bidegorris": bidegorris,\
            "gj_air": gj_air,"gj_noise": gj_noise, "gj_temp": gj_temp, "gj_hum": gj_hum, "gj_vel": gj_vel,\
            'center': [new_center_lon, new_center_lat],'zoom':new_center_zoom} 

            return render(request, 'analisis.html', context)

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
    "gj_air": gj_vacio,"gj_noise": gj_vacio, "gj_temp": gj_vacio, "gj_hum": gj_vacio, "gj_vel": gj_vacio,\
    'center': [config.lon, config.lat],'zoom':config.zoom}  

    return render(request, 'analisis.html', context)    

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Vista de CONSULTA: Consulta avanzada                            #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
def consulta(request):
    # Retrieve config
    config = Config.objects.get(name="base_config")

    # Gestionar Bidegorris    
    kml_tracks = BikeLane.objects.all()
    bidegorris = tracklist_to_geojson(kml_tracks, "bidegorris")
    consulta_vacia = consulta_invalida = 0 # para alerta por consulta vacía
    dtour_l = []
    sensor_air = Sensor.objects.get(sensor_id= 87) # Sensor PM 2.5
    sensor_noise = Sensor.objects.get(sensor_id= 53) # Sensor Noise (dBA)
    sensor_temp = Sensor.objects.get(sensor_id= 55) # Sensor Temperatura (ºC)
    sensor_hum = Sensor.objects.get(name= "SHT31 - Humidity") # Sensor Humedad ()


    # If this is a POST request then process the Form data
    # Sacamos los tracks correspondientes de la consulta 
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = MultipleDateTimeRangeForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # Obtenemos la info del formulario
            try:
                dates = form.clean_range_datetime()
            except:
                consulta_invalida = 1
            if (not consulta_invalida):

                bbox_ne_lon = form.cleaned_data["NE_lon"]
                bbox_ne_lat = form.cleaned_data["NE_lat"]
                bbox_sw_lon = form.cleaned_data["SW_lon"]
                bbox_sw_lat = form.cleaned_data["SW_lat"]
                # Volvemos a crear el formulario para que se vean las fechas que hemos metido
                proposed_start_date = dates[0][0]
                proposed_end_date = dates[0][1]

                form = MultipleDateTimeRangeForm(initial={'since_datetime': proposed_start_date,
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
                
                for date in dates:
                    if not date[0]:
                        date[0] = timezone.now() - timezone.timedelta(seconds=1)
                        date[1] = timezone.now()

                tracks_api = Track.objects.filter(end_time__range=[dates[0][0], dates[0][1]]).filter(mlstring__contained=geom)\
                .union(Track.objects.filter(end_time__range=[dates[1][0], dates[1][1]]).filter(mlstring__contained=geom))\
                .union(Track.objects.filter(end_time__range=[dates[2][0], dates[2][1]]).filter(mlstring__contained=geom))\
                .union(Track.objects.filter(end_time__range=[dates[3][0], dates[3][1]]).filter(mlstring__contained=geom))\
                .union(Track.objects.filter(end_time__range=[dates[4][0], dates[4][1]]).filter(mlstring__contained=geom))
                print(1)
                tracks_device = Track.objects.filter(end_time__range=[dates[0][0], dates[0][1]]).filter(lstring__contained=geom)\
                .union(Track.objects.filter(end_time__range=[dates[1][0], dates[1][1]]).filter(lstring__contained=geom))\
                .union(Track.objects.filter(end_time__range=[dates[2][0], dates[2][1]]).filter(lstring__contained=geom))\
                .union(Track.objects.filter(end_time__range=[dates[3][0], dates[3][1]]).filter(lstring__contained=geom))\
                .union(Track.objects.filter(end_time__range=[dates[4][0], dates[4][1]]).filter(lstring__contained=geom))
                tracks = tracks_api.union(tracks_device)
                for t in tracks:
                    dtour_qs = Dtour.objects.filter(track=t)
                    if dtour_qs:
                        for d in dtour_qs:
                            dtour_l.append(d)
                gj_dtours = tracklist_to_geojson(dtour_l, "dtours")
                gj_tracks = tracklist_to_geojson(tracks,"tracks")     
                print(2)
                print(len(tracks))

                if(len(tracks)>0):
                    measurements_air = Measurement.objects.filter(sensor=sensor_air).filter(time__range=[dates[0][0], dates[0][1]]).filter(point__contained=geom)\
                    .union(Measurement.objects.filter(sensor=sensor_air).filter(time__range=[dates[1][0], dates[1][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_air).filter(time__range=[dates[2][0], dates[2][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_air).filter(time__range=[dates[3][0], dates[3][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_air).filter(time__range=[dates[4][0], dates[4][1]]).filter(point__contained=geom))
                    print(3)
                    measurements_noise = Measurement.objects.filter(sensor=sensor_noise).filter(time__range=[dates[0][0], dates[0][1]]).filter(point__contained=geom)\
                    .union(Measurement.objects.filter(sensor=sensor_noise).filter(time__range=[dates[1][0], dates[1][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_noise).filter(time__range=[dates[2][0], dates[2][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_noise).filter(time__range=[dates[3][0], dates[3][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_noise).filter(time__range=[dates[4][0], dates[4][1]]).filter(point__contained=geom))
                    print(4)
                    measurements_temp = Measurement.objects.filter(sensor=sensor_temp).filter(time__range=[dates[0][0], dates[0][1]]).filter(point__contained=geom)\
                    .union(Measurement.objects.filter(sensor=sensor_temp).filter(time__range=[dates[1][0], dates[1][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_temp).filter(time__range=[dates[2][0], dates[2][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_temp).filter(time__range=[dates[3][0], dates[3][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_temp).filter(time__range=[dates[4][0], dates[4][1]]).filter(point__contained=geom))
                    print(5)
                    measurements_hum = Measurement.objects.filter(sensor=sensor_hum).filter(time__range=[dates[0][0], dates[0][1]]).filter(point__contained=geom)\
                    .union(Measurement.objects.filter(sensor=sensor_hum).filter(time__range=[dates[1][0], dates[1][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_hum).filter(time__range=[dates[2][0], dates[2][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_hum).filter(time__range=[dates[3][0], dates[3][1]]).filter(point__contained=geom))\
                    .union(Measurement.objects.filter(sensor=sensor_hum).filter(time__range=[dates[4][0], dates[4][1]]).filter(point__contained=geom))
                    print(6)

                    print(len(measurements_air))
                    print(len(measurements_noise))
                    print(len(measurements_temp))
                    print(len(measurements_hum))
                    gj_air = measurements_to_geojson(measurements_air)
                    gj_noise = measurements_to_geojson(measurements_noise)
                    gj_temp = measurements_to_geojson(measurements_temp)
                    gj_hum = measurements_to_geojson(measurements_hum)

                    print(7)
                
                if not tracks:
                    consulta_vacia = 1
                    gj_air = gj_hum = gj_temp = gj_noise = empty_geojson()
                else:
                    consulta_vacia = 0
            else:
                gj_tracks = gj_dtours = gj_air = gj_noise = gj_temp = gj_hum = empty_geojson()
                new_center_lon = config.lon
                new_center_lat = config.lat
                new_center_zoom = config.zoom
                proposed_start_date = datetime.date.today() - datetime.timedelta(weeks=52)
                proposed_end_date = timezone.now()
                proposed_sw = Point(-3, 40)
                proposed_ne = Point(-1, 44)
                form = MultipleDateTimeRangeForm(initial={'since_datetime': proposed_start_date,
                'until_datetime':proposed_end_date,'NE_lon': proposed_ne[0],
                'NE_lat': proposed_ne[1],'SW_lon': proposed_sw[0],'SW_lat': proposed_sw[1]})
            context = { 'form': form, 'consulta_vacia': consulta_vacia,\
            'gj_tracks': gj_tracks, "gj_dtours": gj_dtours, "gj_bidegorris": bidegorris,\
            "gj_air": gj_air,"gj_noise": gj_noise, "gj_temp": gj_temp, "gj_hum": gj_hum,\
            'center': [new_center_lon, new_center_lat],'zoom':new_center_zoom} 

            return render(request, 'consulta.html', context)
    
    # Display de form y mapa vacíos 
    # If this is a GET (or any other method) create the default form.
    else:
        proposed_start_date = datetime.date.today() - datetime.timedelta(weeks=52)
        proposed_end_date = timezone.now()
        proposed_sw = Point(-3, 40)
        proposed_ne = Point(-1, 44)
        form = MultipleDateTimeRangeForm(initial={'since_datetime': proposed_start_date,
        'until_datetime':proposed_end_date,'NE_lon': proposed_ne[0],
        'NE_lat': proposed_ne[1],'SW_lon': proposed_sw[0],'SW_lat': proposed_sw[1]})

    gj_vacio = empty_geojson()
    context = { 'form': form, 'consulta_vacia': consulta_vacia,\
    'gj_tracks': gj_vacio, "gj_dtours": gj_vacio, "gj_bidegorris": gj_vacio,\
    "gj_air": gj_vacio,"gj_noise": gj_vacio, "gj_temp": gj_vacio, "gj_hum": gj_vacio,\
    'center': [config.lon, config.lat],'zoom':config.zoom}  

    return render(request, 'consulta.html', context)    


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
            for sck_id in kit_ids:
                calc_new_track(sck_id, "10s")

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

