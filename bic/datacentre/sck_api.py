import json
import requests 
from .models import SCK_device, Sensor, Measurement
from django.contrib.gis.geos import Point

# ID Kit de Ander = 13535
# UUID de Ander = b4b060cb-b4bd-48f6-b60b-ac09799133db
# ID Kit de Diego = 13524
# UUID de Diego = 829e7acd-7f7a-4f19-9197-2e590561e741

# 3 llamadas interesantes (destacables de momento):
# -------------------------------------------------
# Get Historical Readings (de un sensor en concreto) https://api.smartcitizen.me/v0/devices/:device_id/readings
# CSV Archive of readings (mail con csv histórico - NEEDS AUTHENTICATION) https://api.smartcitizen.me/v0/devices/:id/readings/csv_archive
# Get Latest Readings (de todo un kit) https://api.smartcitizen.me/v0/devices/:id
def check_devices():
    # TODO sacar devices y hacer llamadas a la API para cada device a ver si hay datos nuevos
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
            sensors_data = data["sensors"]
            for sensor in sensors_data:
                id_sensor = sensor["id"]
                name = sensor["name"]
                value = sensor["value"]
                unit = sensor["unit"]
                if id_sensor not in id_sensor_list:
                    # Si no existe el tipo de sensor, crear sensor
                    new_sensor = Sensor(sensor_id=id_sensor, device=device, name=sensor["name"])
                    new_sensor.save()   
                # Sacamos los datos para efectuar la nueva medida (Measurement)            
                # TODO chequear si el measurement que comprobamos es nuevo
                # Si es measurement nuevo --> creamos nuevo registro
                new_meas = Measurement(sensor = Sensor.objects.get(pk=id_sensor), units=unit, value=value, point=Point(0,0), time=timestamp)
                new_meas.save()
                # Si no es measurement nuevo no hacemos nada
                reading = {timestamp, id_sensor, name, value}
                readings.append(reading)
        else:
            print("NOT a 200 answer code") #TODO handle this exception

        print(readings)
        

