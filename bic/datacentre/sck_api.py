import json
import requests 
from .models import SCK_device, Sensor, Measurement, Track, BikeLane, Trackpoint
from django.contrib.gis.geos import Point, LineString, MultiLineString, GEOSGeometry, WKTWriter
from .utils import calc_dtours

    
# generar los tracks con la info de la API SC        
def generate_tracks():
    devices = SCK_device.objects.all()
    gps_lat_id = 125
    gps_lon_id = 126

    kml_tracks = BikeLane.objects.all()
    polys = [] 
    for track in kml_tracks:
        polys.append(track.poly)

    for device in devices:
        lat_readings = []
        lon_readings = []
        timestamp_readings = []
        linestring = ""
        # estos tendrán que ser parámetros que pasemos nosotros
        # ------------------
        rollup = "1m"
        from_dt = "2021-05-10"
        to_dt = "2021-05-19"
        # -----------------

        # Llamada LATITUD
        # ----------------    
        url = "https://api.smartcitizen.me/v0/devices/" + str(device.sck_id) +\
        "/readings?sensor_id=" + str(gps_lat_id) + "&rollup=" + rollup + \
        "&from=" + from_dt + "&to=" + to_dt 
        resp = requests.get(url)

        if resp.status_code == 200: # Existe el device y da respuesta
            j = json.loads(resp.text)
            data = j["readings"]
            for reading in data:
                lat_readings.append(reading[1]) # metemos latitud            
        else:
            print("API ERROR: NOT a 200 answer code") #TODO handle this exception better
            print(resp)
        
        # Llamada LONGITUD
        # ----------------    
        url = "https://api.smartcitizen.me/v0/devices/" + str(device.sck_id) +\
        "/readings?sensor_id=" + str(gps_lon_id) + "&rollup=" + rollup + \
        "&from=" + from_dt + "&to=" + to_dt 
        resp = requests.get(url)

        if resp.status_code == 200: # Existe el device y da respuesta
            hayTrack = True
            j = json.loads(resp.text)
            data = j["readings"]
            end_time = data[0][0] # Primer punto = último del track
            start_time = data[len(data)-1][0] # Último punto = primero del track
            for reading in data:
                timestamp_readings.append(reading[0]) # metemos timestamp
                lon_readings.append(reading[1]) # metemos longitud
        else:
            hayTrack = False
            print("API ERROR: NOT a 200 answer code") #TODO handle this exception better
        
        if hayTrack:
            # crear_track(lat_readings, lon_readings, timestamp_readings)
            points_track = []

            if len(lon_readings) > 2:
                linestring = LineString((lon_readings[0], lat_readings[0]), (lon_readings[1], lat_readings[1]), srid=4326) # evitar error de constructor LineString
            i=0
            # creamos array de puntos y linestring
            while i<len(lon_readings): 
                pnt = Point(lon_readings[i],lat_readings[i])
                points_track.append(pnt)
                if i>2:
                    linestring.append((pnt[0], pnt[1]))
                i+=1
            linestring.transform(3035) # Proyección europea EPSG:3035 https://epsg.io/3035 
            distance = linestring.length
            name_track = str(device.sck_id) + "_" + end_time
            new_track = Track(name=name_track, start_time=start_time, end_time=end_time, distance=distance, lstring=linestring, device=device)
            new_track.save()
            i=0
            while i<len(points_track):
                Trackpoint(track=new_track, time=timestamp_readings[i], point=points_track[i]).save()
                i += 1
            pr_update = "Uploading TRACK ..." + str(new_track)
            print(pr_update)

            calc_dtours(polys, linestring, new_track)
            map_measurements(new_track, device.sck_id)
        

# Given a track and device.sck_id --> Map  Measurements(temperature, air, noise) with Trackpoints
def map_measurements(track, device_id):
    device = SCK_device.objects.get(sck_id=device_id)
    trkpts = Trackpoint.objects.filter(track=track) #Approach 1
    rollup = "1m"
    id_sensor_list = [53,55,87,88,89]
    readings = []
    for sensor_id in id_sensor_list:
        url = "https://api.smartcitizen.me/v0/devices/" + str(device_id) +\
        "/readings?sensor_id=" + str(sensor_id) + "&rollup=" + rollup + \
        "&from=" + track.start_time + "&to=" + track.end_time 
        resp = requests.get(url)

        sensor = Sensor.objects.get(sensor_id=sensor_id)
        if resp.status_code == 200: # Existen las medidas en el track
            j1 = json.loads(resp.text)
            data = j1["readings"]
            for reading in data:
                timestamp = reading[0]
                value = reading[1]
                trackpoint = Trackpoint.objects.get(track=track, time=timestamp) # Approach 2
                new_meas = Measurement(sensor= sensor, device=device, trkpoint=trackpoint, time= timestamp, value=value, point=trackpoint.point) 
                new_meas.save()
        else:
            print("NOT a 200 answer code") 



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
                    # print(readings)
                reading = {timestamp, id_sensor, sensor_name, value}
                readings.append(reading)
            print("Número de lecturas nuevas: " + str(contador_medidas))

        else:
            print("NOT a 200 answer code") #TODO handle this exception better

