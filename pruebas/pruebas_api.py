import requests
import json

url = "https://api.smartcitizen.me/v0/devices/" + str(14061) +\
    "/readings?sensor_id=" + str(126) + "&rollup=" + "10s" + \
        "&from=" + "2021-07-26T15:01:00" + "&to=" + "2021-07-26T15:01:30"

resp = requests.get(url)

if resp.status_code == 200:
    j = json.loads(resp.text)
    dataLon = j["readings"]
else:
    print("API ERROR: NOT a 200 answer code")
    
url = "https://api.smartcitizen.me/v0/devices/" + str(14061) +\
        "/readings?sensor_id=" + str(125) + "&rollup=" + "10s" + \
        "&from=" + "2021-07-26T15:01:00" + "&to=" + "2021-07-26T15:01:30"
resp = requests.get(url)

# Chequeamos los valores desde el último checking
# y si varían mandamos los límites al método de construir track

if resp.status_code == 200: # Existe el device y da respuesta       
    j = json.loads(resp.text)
    dataLat = j["readings"]

    print("LAT")
    for element in dataLat:
        print(element)

    print("LON")
    for element in dataLon:
        print(element)
    print("LENGTHS")
    print(len(dataLat))
    print(len(dataLon))

    limits = []
    hayNewTrack = False
    last_lat = dataLat[0][1] # Primer punto = último del track ()
    last_lon = dataLon[0][1]
    last_timestamp = dataLat[0][0] # Primer timestamp = último del track
    i=1

    if len(dataLon) > len(dataLat): # si uno es más grande que el otro, cogemos el mayor para iterar
        maxMedidas = dataLon 
    elif len(dataLon) < len(dataLat):
        maxMedidas = dataLat
    else:
        maxMedidas = dataLon # si son iguales nos da igual y cogemos cualquiera

    while i<maxMedidas: # desde punto 2 comparar si es igual o cambia muy poco  
        point2 = dataLat[i][1]
        try: # ESTO POR QUÉ? --> El 26 de julio de 2021 a las 15:01:25 se guardó en los servidores de SC la latitud pero no la longitud del dispositivo
            point2lon = dataLon[i][1]
            
        except IndexError:
            point2lon = dataLon[i-1][1]
        time2 = dataLat[i][0]


        i = i + 1