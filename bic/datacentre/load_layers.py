# Cargador de Layers (GPX, KML...)
# From geodjango tutorial = how to load geospatial data with LayerMapping 
# https://docs.djangoproject.com/en/3.1/ref/contrib/gis/tutorial/ - LayerMapping
# cada layer necesita una tabla 
from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import GEOSGeometry, LineString, WKTWriter, Point
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.measure import D, Distance
from django.contrib.gis.db.models.functions import Length
from django.utils import timezone
from .models import Track, BikeLane, Dtour, SCK_device, Sensor, Measurement, Trackpoint
from .utils import parse_gpx, calc_dtours, calc_velocity_between_2_points

import sys, os
import gpxpy # For manipulating gpx files from python
import random
import requests
import json
import datetime
import logging

logger = logging.getLogger(__name__)

# # # # # # #
# LOAD GPX  #
# # # # # # #

# Mapear atributos modelo Django contra fields del layer del DataSource 
track_mapping = {
    'mlstring':'MultiLineString',
}

# Solo carga tracks, si queremos trackpts, wpts, etc. hay que cambiar el método
def load_gpx_lm(verbose=True):
    """Recorre la carpeta datacentre/data/gpx e introduce en la BD los tracks de los GPX + dtours asociados

    Hace uso de LayerMapping --> Docs en https://docs.djangoproject.com/en/3.1/ref/contrib/gis/layermapping/
    """

    dir_gpx_data = Path("/home/eguiwow/github/BIC/bic/datacentre/data/gpx") # Directorio donde están de momento guardados los GPXs
    for filepath in dir_gpx_data.glob( '*.gpx' ):
        print(filepath)
        lm = LayerMapping(Track, str(filepath), track_mapping, layer=2, transform=False) # Layer = 2 -> Layer = track de un GPX
        lm.save(strict=False, verbose = verbose) # strict = True antes. Esto lo que hace es que si hay un fallo para la ejecución

# Solo carga tracks, si queremos trackpts, wpts, etc. hay que cambiar el método
def load_gpx_from_folder(verbose=True):
    """Recorre la carpeta datacentre/data/gpx e introduce en la BD los tracks de los GPX + dtours asociados

    Sin usar LayerMapping
    """    

    kml_tracks = BikeLane.objects.all()
    polys = [] 
    for track in kml_tracks:
        polys.append(track.poly)

    dir_gpx_data = Path("/home/eguiwow/github/BIC/bic/datacentre/data/extra_gpx") # Directorio donde están de momento guardados los GPXs
    for filepath in dir_gpx_data.glob( '*.gpx' ):
        gpx_file = open(filepath, 'r')
        data = parse_gpx(gpx_file)
        lstring = GEOSGeometry(data[2], srid=4326)
        lstring.transform(3035) # Proyección europea EPSG:3035 https://epsg.io/3035 
        new_track = Track(name=filepath.name, start_time=data[0], end_time=data[1], distance=lstring.length, mlstring=data[2])
        new_track.save()
        pr_update = "Uploading TRACK ..." + str(new_track)
        logger.info(pr_update)
        # calculamos dtours
        calc_dtours(polys, lstring, new_track)

def load_gpx_from_file(gpx_file, verbose=True):
    """ Carga el archivo GPX (gpx_file) pasado en forma de track + dtour en la BD


    Parameters
    ----------
    gpx_file : 
        archivo GPX abierto

    Returns
    -------
    boolean :
        True si es GPX y procesable
        False si otro archivo o no procesable
    """
    kml_tracks = BikeLane.objects.all()
    polys = [] 
    for track in kml_tracks:
        polys.append(track.poly)
    try:
        data = parse_gpx(gpx_file)
        lstring = GEOSGeometry(data[2], srid=4326)
        lstring.transform(3035) # Proyección europea EPSG:3035 https://epsg.io/3035 
        new_track = Track(name=gpx_file.name, start_time=data[0], end_time=data[1], distance=lstring.length, mlstring=data[2])
        new_track.save()
        last_point = False
        velocity = 0
        for point in data[3]:
            delay = False
            if last_point != False:
                velocity = calc_velocity_between_2_points(point[0], last_point[0], point[1], last_point[1])
                if velocity < 1: # if velocity is less than 1km/h then it's a delay point
                    delay = True
            Trackpoint(track=new_track, time_tracks=point[1], point=point[0], velocity=velocity, delay=delay).save()
            last_point = point
 

        pr_update = "Uploading TRACK and associated TRACKPOINTS..." + str(new_track)
        logger.info(pr_update)
        calc_dtours(polys, lstring, new_track)
        return True

    except IOError:
        type, value, traceback = sys.exc_info()
        print('Error opening %s: %s' % (value.filename, value.strerror))
        return False

# # # # # # #
# LOAD KML  #
# # # # # # #

def get_feat_property(feat):
    """ Dada una feature --> devuelve property"""
    property = {
        'name': feat.get('Name'),
    }
    return property

# Ahora la ruta es fija
def load_kml(verbose=True):
    """ Recorre la carpeta/data/kml --> introduce en la BD los linestrings de los KML 
    https://medium.com/@kitcharoenpoolperm/geodjango-import-data-from-kml-file-de110dba1f60 """
    # Ruta al archivo que queremos introducir en la BD BikeLanes
    kml_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'kml', 'bidegorris.kml'),)
    # Reading Data by DataSource
    ds = DataSource(kml_file)
    # Writes the Well-Known Text representation of a Geometry.
    wkt_w = WKTWriter()
    # Iterating Over Layers
    for layer in ds:
        for feat in layer:
            if(feat.geom.geom_type.name.startswith('Line')):
                # Get the feature geometry.
                geom = feat.geom
                # get the feature property
                property = get_feat_property(feat)
                if (len(geom.coords) >= 2 ):
                    # Make a GEOSGeometry object
                    lstring = GEOSGeometry(wkt_w.write(geom.geos), srid=4326)
                    lstring.transform(3035)
                    dist = lstring.length
                    line = BikeLane.objects.create(
                        name = property['name'],
                        distance = dist,
                        lstring = lstring,
                        # ST_Buffer() --> Poligonizamos los bidegorris a una anchura de 10m
                        # https://www.usna.edu/Users/oceano/pguth/md_help/html/approx_equivalents.htm#:~:text=0.00001%C2%B0%20%3D%201.11%20m 
                        poly = lstring.buffer(10,quadsegs=8)                    
                    )
                    logger.info(line)

def load_false_measurements():
    """ Introduce medidas de sensórica de prueba en la BD"""
    device = SCK_device.objects.get(sck_id=999)
    sensorNoise = Sensor.objects.get(sensor_id=53)
    sensorTemp = Sensor.objects.get(sensor_id=55)
    sensorPM = Sensor.objects.get(sensor_id=87)

    avg_lat = 43.26299
    avg_lon = -2.93522

    i = 0
    while i<100:

        lon = random.uniform(-0.0095, 0.0095) + avg_lon            
        lat = random.uniform(-0.0095, 0.0095) + avg_lat
        point = Point(lon,lat)
        valueNoise = random.randrange(30,100)
        valuePM = random.randrange(150)                        
        valueTemp = random.randrange(-5, 45)                 

        print("Point: " + str(point))
        print("Noise: " + str(valueNoise))
        print("Temp: " + str(valueTemp))
        print("PM: " + str(valuePM))
        new_measNoise = Measurement(sensor= sensorNoise, device=device, value=valueNoise, point=point).save()
        new_measTemp = Measurement(sensor= sensorTemp, device=device, value=valueTemp, point=point).save()
        new_measPM = Measurement(sensor= sensorPM, device=device, value=valuePM, point=point).save()

        i+=1


def load_humidity_measurements():
    """ Introduce medidas de sensórica de prueba en la BD"""
    device = SCK_device.objects.get(sck_id=14061)
    sensorHum = Sensor.objects.get(sensor_id=56)
    
    dt_timestamps_tracks = [] # Primero el más reciente, último el más viejo
    tracks = Track.objects.all().order_by('-end_time')
    
    for track in tracks:
        dt_timestamps_tracks.append([track.start_time, track.end_time, track.id])

    today = timezone.localtime(timezone.now())
    time_limits = []
    # FROM_DATETIME
    try: 
        first_track = Track.objects.filter(mlstring__isnull=True).earliest('end_time')
        last_track = Track.objects.filter(mlstring__isnull=True).latest('end_time')        
        dt_first_track_end_time = first_track.end_time
        from_dt = dt_first_track_end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    except Track.DoesNotExist: 
        dt_first_track_end_time = datetime.datetime.now() - datetime.timedelta(days=365)
        from_dt = dt_first_track_end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # GET ALL READINGS HUMIDITY 
    today_str = today.strftime("%Y-%m-%dT%H:%M:%SZ")
    url = "https://api.smartcitizen.me/v0/devices/" + str(14061) +\
        "/readings?sensor_id=" + str(56) + "&rollup=" + "10s" + \
        "&from=" + from_dt + "&to=" + today_str
    resp = requests.get(url)
    if resp.status_code == 200: # Existen las medidas en el track
        j1 = json.loads(resp.text)
        data = j1["readings"]                    
    else:
        logger.info("NOT a 200 answer code") 

    # GET HUMIDITY MEASUREMENTS WITH TRACKPOINTS
    cont_puntos_malos = 0
    cont_medidas = 0

    dt_last_track_end_time = last_track.end_time
    dt_last_track_start_time = last_track.start_time
    del dt_timestamps_tracks[0] # eliminamos último track de la lista

    for t in data:
        dt_measurement = datetime.datetime.strptime(t[0], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc)
        if dt_measurement <= dt_last_track_end_time and dt_measurement >=dt_last_track_start_time:

            # AÑADIMOS MEASUREMENT NUEVO
            try: 
                trackpoint = Trackpoint.objects.get(track=track, time=dt_measurement)
                Measurement(sensor=sensorHum, time=dt_measurement, device=device, value=t[1], point=trackpoint.point, trkpoint=trackpoint).save()
                cont_medidas += 1

            except Trackpoint.DoesNotExist: 
                cont_puntos_malos += 1      

        elif dt_measurement < dt_last_track_start_time:
            dt_last_track_start_time = dt_timestamps_tracks[0][0]
            dt_last_track_end_time = dt_timestamps_tracks[0][1]
            track = Track.objects.get(id=dt_timestamps_tracks[0][2])

            del dt_timestamps_tracks[0]
        
        if cont_medidas % 1000 == 0:
            print(str(cont_medidas) + "medidas subidas")

    print("Total medidas subidas " + str(cont_medidas))



# # # # #
# MAIN  #
# # # # #

def main():
    #load_gpx_from_folder()
    load_kml()

if __name__ == '__main__':
    main()

