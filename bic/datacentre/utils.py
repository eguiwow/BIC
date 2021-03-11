from django.contrib.gis.geos import GEOSGeometry # For lazy geometries

# TODO Returns an empty but formatted GeoJSON
def empty_geojson():
    gj_tracks = []
    gj_tracks.append("{\"type\": \"FeatureCollection\",\"features\": []}")
    formatted_geojson = ''.join(gj_tracks) #TODO cambiar nombre a esta variable a geojson_trks o algo así
    return formatted_geojson

# Given a list of tracks returns a formatted GeoJSON containing those tracks [MULTILINESTRING] !
def tracklist_to_geojson(tracks):
    gj_tracks = []
    gj_tracks.append("{\"type\": \"FeatureCollection\",\"features\": [")

    for track in tracks:
        # print("***TRACKS***")
        # print ('MLString de track', track.mlstring) #Sacamos el SRID y una lista de coordenadas 
        gj_tracks.append("{\"type\": \"Feature\",\"geometry\": ") #Inicio de una Feature
        gj_tracks.append(GEOSGeometry(track.mlstring, srid=4326).geojson) #Añadimos a la lista el geojson pertinente
        gj_tracks.append("},") # Cerramos el Feature (track) 
        
        # TODO parte de Properties
        # gj_tracks.append(", \"properties\": { } }") 
        
    if len(gj_tracks) > 1:
        gj_tracks = gj_tracks[:-1] # Quitamos la coma para el último track
        gj_tracks.append("}")

    gj_tracks.append("]}") # Cerramos el GeoJSON 
    formatted_geojson = ''.join(gj_tracks) #TODO cambiar nombre a esta variable a geojson_trks o algo así
    
    return formatted_geojson