import json
import requests 
from django.utils import timezone
from .models import SCK_device, Sensor, Measurement, Track, BikeLane, Trackpoint
from django.contrib.gis.geos import Point, LineString, MultiLineString, GEOSGeometry, WKTWriter
from .utils import calc_dtours
from datetime import date
import datetime
import logging

logger = logging.getLogger(__name__)

# Given a track and device.sck_id --> Map  Measurements(temperature, air, noise) with Trackpoints
def map_measurements(track, device_id, rollup):
    device = SCK_device.objects.get(sck_id=device_id)
    id_sensor_list = [53,55,87,88,89] # noise, temperature, PM10, PM5, PM2.5

    for sensor_id in id_sensor_list:
        url = "https://api.smartcitizen.me/v0/devices/" + str(device_id) +\
        "/readings?sensor_id=" + str(sensor_id) + "&rollup=" + rollup + \
        "&from=" + track.start_time + "&to=" + track.end_time 
        resp = requests.get(url)
        
        sensor = Sensor.objects.get(sensor_id=sensor_id)
        if resp.status_code == 200: # Existen las medidas en el track
            j1 = json.loads(resp.text)
            data = j1["readings"]                    
        else:
            logger.info("NOT a 200 answer code") 
        
        cont_puntos_malos = 0
        for reading in data:
            timestamp = reading[0]
            value = reading[1]
            try: 
                trackpoint = Trackpoint.objects.get(track=track, time=timestamp) # Approach 2
                new_meas = Measurement(sensor= sensor, device=device, trkpoint=trackpoint, time= timestamp, value=value, point=trackpoint.point) 
                new_meas.save()
            except Trackpoint.DoesNotExist: 
                cont_puntos_malos += 1      
        logger.info("Uploading measurements from sensor " + str(sensor_id))          

    logger.info("Puntos eliminados por mala señal GPS " + str(cont_puntos_malos))
    cont_puntos_malos = 0



# Check for new sensors and for new measurements of stored devices
def check_devices():
    devices = SCK_device.objects.all()
    sensors = Sensor.objects.all()
    contador_medidas = 0
    id_sensor_list = []
    for sensor in sensors: 
        id_sensor_list.append(sensor.sensor_id)
    for device in devices:
        readings = []
        url = "https://api.smartcitizen.me/v0" + "/devices/" + str(device.sck_id) +"?pretty=true" # Saca los últimos valores recogidos de cada device (no hace falta autorización)
        resp = requests.get(url)

        # readings = get_readings_from_device()
        if resp.status_code == 200: # Existe el device y da respuesta
            j1 = json.loads(resp.text)
            timestamp = j1["last_reading_at"]
            data = j1["data"]
            location = data["location"]
            sensor_point = None
            if location:
                sensor_point = Point(location["longitude"], location["latitude"])
            sensors_data = data["sensors"]
            for sensor in sensors_data:
                id_sensor = sensor["id"]
                sensor_name = sensor["name"]
                sensor_description = sensor["description"]
                value = sensor["value"]
                unit = sensor["unit"]
                if id_sensor not in id_sensor_list:
                    # Si no existe el tipo de sensor, crear sensor
                    new_sensor = Sensor(sensor_id=id_sensor, name=sensor_name, description=sensor_description, units=unit)
                    new_sensor.save()   
                # Sacamos los datos para efectuar la nueva medida (Measurement)            
                measurements = Measurement.objects.filter(sensor=Sensor.objects.get(pk=id_sensor)).filter(device=device).filter(time=timestamp) # Si es measurement nuevo --> creamos nuevo registro
                if not measurements: # Si es measurement nuevo --> guardamos
                    new_meas = Measurement(sensor = Sensor.objects.get(pk=id_sensor), device=device, value=value, point=sensor_point, time=timestamp)
                    new_meas.save()
                    contador_medidas += 1
                reading = {timestamp, id_sensor, sensor_name, value}
                readings.append(reading)
            logger.info("Número de lecturas nuevas: " + str(contador_medidas))

        else:
            logger.info("NOT a 200 answer code") #TODO handle this exception better


# generar los tracks con la info de la API SC        
def generate_tracks_time(from_dt, to_dt, rollup, sck_id):
    gps_lat_id = 125
    gps_lon_id = 126

    device = SCK_device.objects.get(sck_id=sck_id)

    kml_tracks = BikeLane.objects.all()
    polys = [] 
    for track in kml_tracks:
        polys.append(track.poly)

    lat_readings = []
    lon_readings = []
    timestamp_readings = []
    linestring = ""
    maxLon = False

    # Llamada LATITUD
    # ----------------    
    url = "https://api.smartcitizen.me/v0/devices/" + str(sck_id) +\
    "/readings?sensor_id=" + str(gps_lat_id) + "&rollup=" + rollup + \
    "&from=" + from_dt + "&to=" + to_dt 
    resp = requests.get(url)

    if resp.status_code == 200: # Existe el device y da respuesta
        j = json.loads(resp.text)
        dataLat = j["readings"]
    else:
        logger.error("API ERROR: NOT a 200 answer code") 
    
    # Llamada LONGITUD
    # ----------------    
    url = "https://api.smartcitizen.me/v0/devices/" + str(sck_id) +\
    "/readings?sensor_id=" + str(gps_lon_id) + "&rollup=" + rollup + \
    "&from=" + from_dt + "&to=" + to_dt 
    resp = requests.get(url)

    if resp.status_code == 200: # Existe el device y da respuesta
        hayTrack = True
        j = json.loads(resp.text)
        dataLon = j["readings"]

    else:
        hayTrack = False
        logger.error("API ERROR: NOT a 200 answer code")
    
    # Limpiamos arrays de valores sueltos (lon / lat)
    # -----------------------------------------------
    if len(dataLon) > len(dataLat): # si uno es más grande que el otro, cogemos el menor para iterar
        minMedidas = len(dataLat)
        maxLon = True
    elif len(dataLon) < len(dataLat):
        minMedidas = len(dataLon)
        maxLon = False
    else:
        minMedidas = len(dataLon) # si son iguales nos da igual y cogemos cualquiera

    if maxLon:
        end_time = dataLon[0][0] # Primer punto = último del track
        start_time = dataLon[len(dataLon)-1][0] # Último punto = primero del track
    else:
        end_time = dataLat[0][0]
        start_time = dataLat[len(dataLat)-1][0] # Último punto = primero del track
    
    difference = len(dataLon)-len(dataLat)

    i = 0
    while abs(difference) > 0:
        while i < (minMedidas-1):
            if maxLon:
                if dataLon[i][0] != dataLat[i][0]:
                    date_time_lon = datetime.datetime.strptime(dataLon[i][0], '%Y-%m-%dT%H:%M:%SZ')
                    date_time_lat = datetime.datetime.strptime(dataLat[i][0], '%Y-%m-%dT%H:%M:%SZ')
                    diff_secs = abs(date_time_lat-date_time_lon)
                    if diff_secs.total_seconds() >= 10:
                        dataLon.pop(i)
                        difference = len(dataLon)-len(dataLat)
                        i = i-1

            else:
                if dataLon[i][0] != dataLat[i][0]:
                    date_time_lon = datetime.datetime.strptime(dataLon[i][0], '%Y-%m-%dT%H:%M:%SZ')
                    date_time_lat = datetime.datetime.strptime(dataLat[i][0], '%Y-%m-%dT%H:%M:%SZ')
                    diff_secs = abs(date_time_lat-date_time_lon)
                    if diff_secs.total_seconds() >= 10:
                        dataLat.pop(i)
                        difference = len(dataLon)-len(dataLat)
                        i = i-1

            i += 1
    # Ahora que hemos limpiado el array, añadimos medidas a lon, lat y timestamp
    for i in range(minMedidas):
        timestamp_readings.append(dataLon[i][0]) # metemos timestamp de cualquiera de los 2
        lon_readings.append(dataLon[i][1]) # metemos longitud
        lat_readings.append(dataLat[i][1]) # metemos latitud          
          

    if hayTrack:
        # crear_track(lat_readings, lon_readings, timestamp_readings)
        points_track = []

        if len(lon_readings) > 2:
            linestring = LineString((lon_readings[0], lat_readings[0]), (lon_readings[1], lat_readings[1]), srid=4326) # evitar error de constructor LineString
        i=0
        
        last_lat = lat_readings[0]
        last_lon = lon_readings[0]
        # creamos array de puntos y linestring
        while i<len(lon_readings):
            if lon_readings[i] != 0 and lat_readings[i] != 0: # Evitamos meter medida cuando pierde señal GPS
                if i < (len(lon_readings)-1):   
                    dif_lat = abs(last_lat-lat_readings[i])
                    dif_lon = abs(last_lon-lon_readings[i])

                    if dif_lat >0.00002 and dif_lon >0.00002 and dif_lat < 0.04 and dif_lon < 0.04: # Solo metemos aquellos puntos que estén a ~<100 m de distancia para evitar puntos con mala señal GPS

                        last_lat = lat_readings[i]
                        last_lon = lon_readings[i]

                        pnt = Point(lon_readings[i],lat_readings[i])
                        points_track.append(pnt)
                        if i>2:
                            linestring.append((pnt[0], pnt[1]))
            #TODO aquí faltaría manejar el último punto del linestring que se pierde ahora mismo
            i+=1
        if linestring != "":
            linestring.transform(3035) # Proyección europea EPSG:3035 https://epsg.io/3035 
            distance = linestring.length
            name_track = str(sck_id) + "_" + end_time
            new_track = Track(name=name_track, start_time=start_time, end_time=end_time, distance=distance, lstring=linestring, device=device)
            new_track.save()
            for i in range(len(points_track)):
                Trackpoint(track=new_track, time=timestamp_readings[i], point=points_track[i]).save()
        
            pr_update = "Uploading TRACK ..." + str(new_track)
            logger.info(pr_update)

            calc_dtours(polys, linestring, new_track)
            map_measurements(new_track, sck_id, rollup)
            return True
        else:
            logger.info("Track demasiado corto (2 puntos o menos)")
            return False


# calcular el rango temporal de sigiente track
def calc_time_limits(sck_id, rollup):
    
    today = timezone.localtime(timezone.now())
    time_limits = []
    # FROM_DATETIME
    try: 
        last_track = Track.objects.filter(end_time__isnull=False).latest('end_time')    
        last_track_datetime = last_track.end_time
        from_dt = last_track_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    except Track.DoesNotExist: 
        last_track_datetime = datetime.datetime.now() - datetime.timedelta(days=365)
        from_dt = last_track_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    # TO_DATE YYYY-mm-dd
    today_str = today.strftime("%Y-%m-%dT%H:%M:%SZ")
    #Llamada datos LON
    url = "https://api.smartcitizen.me/v0/devices/" + str(sck_id) +\
        "/readings?sensor_id=" + str(126) + "&rollup=" + rollup + \
        "&from=" + from_dt + "&to=" + today_str
    resp = requests.get(url)
    if resp.status_code == 200:
        j = json.loads(resp.text)
        dataLon = j["readings"]
    else:
        logger.error("API ERROR: NOT a 200 answer code")
        return False
    #Llamada datos LAT
    url = "https://api.smartcitizen.me/v0/devices/" + str(sck_id) +\
        "/readings?sensor_id=" + str(125) + "&rollup=" + rollup + \
        "&from=" + from_dt + "&to=" + today_str
    resp = requests.get(url)

    if resp.status_code == 200: # Existe el device y da respuesta       
        j = json.loads(resp.text)
        dataLat = j["readings"]
    else:
        logger.error("API ERROR: NOT a 200 answer code")
        return False
    
    # Chequeamos los valores desde el último checking
    # y si varían mandamos los límites al método de construir track
    limits = []
    hayNewTrack = False
    last_lat = dataLat[0][1] # Primer punto = último del track ()
    last_lon = dataLon[0][1]
    last_timestamp = dataLat[0][0] # Primer timestamp = último del track
    maxLon = False    

    # Mismo número de datos lat y lon? --> Limpiamos arrays de valores sueltos
    if len(dataLon) > len(dataLat): # si uno es más grande que el otro, cogemos el mayor para iterar
        minMedidas = len(dataLat)
        maxLon = True
    elif len(dataLon) < len(dataLat):
        minMedidas = len(dataLon)
        maxLon = False
    else:
        minMedidas = len(dataLon) # si son iguales nos da igual y cogemos cualquiera

    difference = len(dataLon)-len(dataLat)
    i = 0

    while abs(difference) > 0:
        while i < (minMedidas-1):
            if maxLon:
                if dataLon[i][0] != dataLat[i][0]:
                    date_time_lon = datetime.datetime.strptime(dataLon[i][0], '%Y-%m-%dT%H:%M:%SZ')
                    date_time_lat = datetime.datetime.strptime(dataLat[i][0], '%Y-%m-%dT%H:%M:%SZ')
                    diff_secs = abs(date_time_lat-date_time_lon)
                    if diff_secs.total_seconds() >= 10:
                        dataLon.pop(i)
                        difference = len(dataLon)-len(dataLat)
                        i = i-1

            else:
                if dataLon[i][0] != dataLat[i][0]:
                    date_time_lon = datetime.datetime.strptime(dataLon[i][0], '%Y-%m-%dT%H:%M:%SZ')
                    date_time_lat = datetime.datetime.strptime(dataLat[i][0], '%Y-%m-%dT%H:%M:%SZ')
                    diff_secs = abs(date_time_lat-date_time_lon)
                    if diff_secs.total_seconds() >= 10:
                        dataLat.pop(i)
                        difference = len(dataLon)-len(dataLat)
                        i = i-1

            i += 1
    
    i = 0
    while i<(minMedidas-1): # desde punto 2 comparar si es igual o cambia muy poco  
        point2lat = dataLat[i][1]
        point2lon = dataLon[i][1]
        time2 = dataLat[i][0]
           
        date_time_last = datetime.datetime.strptime(last_timestamp, '%Y-%m-%dT%H:%M:%SZ')
        date_time2 = datetime.datetime.strptime(time2, '%Y-%m-%dT%H:%M:%SZ')

        duration = date_time_last - date_time2 # porque el primer punto es el último del track                       
        duration_in_s = duration.total_seconds() 
        if duration_in_s > 600: # si son más de 10 mins guardamos los limits y pasamos a otro track
            if hayNewTrack: 
                end_time = limits[0]
                start_time = limits[len(limits)-1]
                track_time_bounds =[start_time, end_time]
                time_limits.append(track_time_bounds)
                limits = []
                hayNewTrack = False

        else:
            dif_lat = abs(point2lat-last_lat)
            dif_lon = abs(point2lon-last_lon)
            if point2lat != 0 and dif_lat >0.00002 and point2lon!=0 and dif_lon >0.00002: # si mayor que 0.0002 
                if dif_lat < 0.05 and dif_lon < 0.05 : # si es mayor que eso la diferencia descartamos
                    hayNewTrack = True
                    limits.append(dataLat[i][0])
        last_lat = point2lat
        last_lon = point2lon
        last_timestamp = time2
        i+=1

    if time_limits: 
        logger.info("Chequeando nuevos tracks\ndesde: " + time_limits[len(time_limits)-1][0] + "\nhasta: " + time_limits[0][1] + "\ncon rollup: " + rollup)
        return time_limits



def calc_new_track(sck_id, rollup):
    time_bounds = calc_time_limits(sck_id, rollup)
    if time_bounds:
        for time_limits in time_bounds:
            if generate_tracks_time(time_limits[0], time_limits[1], rollup, sck_id):
                logger.info("Successfully updated new track")
            else:
                logger.info("NO track updated")
    else:
        logger.info("NO tracks since last fetch")




