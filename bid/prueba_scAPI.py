import json
import requests
from requests.auth import HTTPBasicAuth 

# Pruebas sobre la API https://developer.smartcitizen.me/?shell#summary

# ID Kit de Ander = 13535
# UUID de Ander = b4b060cb-b4bd-48f6-b60b-ac09799133db
# ID Kit de Diego = 13524
# UUID de Diego = 829e7acd-7f7a-4f19-9197-2e590561e741

# 3 llamadas interesantes (destacables de momento):
# -------------------------------------------------
# Get Historical Readings (de un sensor en concreto) https://api.smartcitizen.me/v0/devices/:device_id/readings
# CSV Archive of readings (mail con csv histórico - NEEDS AUTHENTICATION) https://api.smartcitizen.me/v0/devices/:id/readings/csv_archive
# Get Latest Readings (de todo un kit) https://api.smartcitizen.me/v0/devices/:id

def main(): # Ejemplo sacado de https://github.com/fablabbcn/smartcitizen-data/blob/master/tests/api/test_api.py
# Device id needs to be as str
    id = 13524
    sensor_id = 88 # PM
    uuid = 'b4b060cb-b4bd-48f6-b60b-ac09799133db' # UUID de Ander = b4b060cb-b4bd-48f6-b60b-ac09799133db
    url = "https://api.smartcitizen.me/v0" + "/devices/" + str(id) +"?pretty=true" # Saca los últimos valores recogidos de cada device (no hace falta autorización)
    resp = requests.get(url)
    # Con autenticación:
    # resp = requests.get(url, auth=HTTPBasicAuth('eguiwan_kenobi','MORElab2020')) # TODO esto es recomendable hacerlo con OAuth
    j = json.loads(resp.text)
    url2 = "https://api.smartcitizen.me/v0/devices/"+str(id)+"/readings?sensor_id=88&rollup=1y" #Sacando readings de un sensor en concreot
    resp2 = requests.get(url2)
    j2 = json.loads(resp2.text)
    
    print(j2)
    
if __name__ == '__main__':
    main()
