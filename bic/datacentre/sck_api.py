import json
import requests 
from .models import SCK_device, Sensor, Measurement
from django.contrib.gis.geos import Point

def check_devices():
    devices = SCK_device.objects.all()
    sensors = Sensor.objects.all()
    id_sensor_list = []
    for sensor in sensors: 
        id_sensor_list.append(sensor.sensor_id)
    for device in devices:
        readings = []
        url = "https://api.smartcitizen.me/v0" + "/devices/" + str(device.sck_id) +"?pretty=true" # Saca los últimos valores recogidos de cada device (no hace falta autorización)
        resp = requests.get(url)
        j1 = json.loads(resp.text)

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
                    new_sensor = Sensor(sensor_id=id_sensor, name=sensor_name, description=sensor_description)
                    new_sensor.save()   
                # Sacamos los datos para efectuar la nueva medida (Measurement)            
                measurements = Measurement.objects.filter(sensor=Sensor.objects.get(pk=id_sensor)).filter(device=device).filter(time=timestamp) # Si es measurement nuevo --> creamos nuevo registro
                if not measurements: # Si es measurement nuevo --> guardamos
                    new_meas = Measurement(sensor = Sensor.objects.get(pk=id_sensor), device=device, units=unit, value=value, point=sensor_point, time=timestamp)
                    new_meas.save()
                    print(readings)
                else: # Si no es measurement nuevo no hacemos nada
                    print("NO HAY MEASUREMENTS NUEVOS") # TODO que esto se indique en la GUI
                reading = {timestamp, id_sensor, sensor_name, value}
                readings.append(reading)
        else:
            print("NOT a 200 answer code") #TODO handle this exception better

# generar los tracks con la info de la API SC        
def generate_tracks():
    return ""

