from django.contrib.gis.geos import GEOSGeometry # For lazy geometries
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import LineString, MultiLineString, Point, MultiPoint
from django.contrib.gis.db.models.functions import Length
from django.contrib.gis.measure import D, Distance
from .models import KML_lstring
import gpxpy

# Returns an empty but formatted GeoJSON
def empty_geojson():
    gj_tracks = []
    gj_tracks.append("{\"type\": \"FeatureCollection\",\"features\": []}")
    formatted_geojson = ''.join(gj_tracks) 
    return formatted_geojson

# Given a list of tracks and a geom_name --> returns a formatted GeoJSON containing those tracks
# with the corresponding Feature for the geom_name
# mlstring --> MULTILINESTRING
# lstring --> LINESTRING
# poly --> POLYGON
# If tracks is empty --> returns an empty GeoJSON 
def tracklist_to_geojson(tracks, geom_name):
    gj_tracks = []
    gj_tracks.append("{\"type\": \"FeatureCollection\",\"features\": [")
    if tracks:
        for track in tracks:
            #Inicio de una Feature
            gj_tracks.append("{\"type\": \"Feature\",\"geometry\": ") 
            #Añadimos a la lista el geojson pertinente
            if geom_name == "poly":
                gj_tracks.append(GEOSGeometry(track.poly, srid=4326).geojson) 
            elif geom_name == "mlstring":
                gj_tracks.append(GEOSGeometry(track.mlstring, srid=4326).geojson) 
            elif geom_name == "lstring":
                gj_tracks.append(GEOSGeometry(track.lstring, srid=4326).geojson)
            elif geom_name == "point":
                del gj_tracks[-1:]
                cont = 0
                puntos_track = get_lista_puntos(track) # Devolver Multipoints
                for punto in puntos_track:
                    if cont == 1: # quitamos la mitad de los puntos
                        gj_tracks.append("{\"type\": \"Feature\",\"geometry\": ") 
                        gj_tracks.append(punto.geojson) # Añadir Point 
                        gj_tracks.append("},")  
                        cont = 0
                    else:
                        cont += 1
                del gj_tracks[-1:]
            else:
                print("ERROR IN PASSING 2nd parameter <geom_name>")
            # Cerramos el Feature (track) 
            gj_tracks.append("},")
            
            # TODO parte de Properties
            # gj_tracks.append(", \"properties\": { } }") 
        
        # Quitamos la coma para el último track
        if len(gj_tracks) > 1:
            gj_tracks = gj_tracks[:-1]
            gj_tracks.append("}")
        
        # Cerramos el GeoJSON 
        gj_tracks.append("]}")
        # Lo unimos en un único String
        formatted_geojson = ''.join(gj_tracks)

    # Si la lista de tracks está vacía, devolvemos un GeoJSON vacío
    else:
        formatted_geojson = empty_geojson()
        print("The tracklist is empty")
    
    return formatted_geojson

# Applies ST_Difference() between a list of tracks and polys (diff = track - poly [mlstring])
# Returns multilinestring[] with properties[dtour_length, ratio dtour/track]
def get_dtours(tracks, polys):
    intersected = False
    gj_dtours = []
    # Abrimos los GeoJSON con sus Features
    gj_dtours.append("{\"type\": \"FeatureCollection\",\"features\": [") 

    if polys:
        for t in tracks:
            if t.distance:
                track_length = t.distance # length del track en m
            track = GEOSGeometry(t.mlstring, srid=4326)
            for i in polys: # sacamos cada poly de la lista
                if track.intersects(i):# if they intersect --> then do the .difference()
                    intersected = True
                    track = track.difference(i) # Guardamos el resultante como nuevo track y guardamos solo al final
            if intersected:
                gj_dtours.append("{\"type\": \"Feature\",") # Abrimos Feature
                dtour = track # Difference = Track - Poly                
                gj_dtours.append("\"geometry\": " + dtour.geojson)
                gj_dtours.append(",")
                
                # Calcular distancia dtours
                geos = GEOSGeometry(dtour)
                geos.transform(3857)
                dtour_length = geos.length #Length(geos) # Length del dtour
                ratio_dtour_to_track = (dtour_length/track_length)*100
                
                # PROPERTIES
                prop_dict = { 'dtour_l' : str(dtour_length), 'ratio' : str(ratio_dtour_to_track) }
                gj_dtours = addProperties(gj_dtours, prop_dict)                

                gj_dtours.append("},") # Cerramos Feature

                intersected = False
                    
        if len(gj_dtours) > 1:
            gj_dtours = gj_dtours[:-1] # Quitamos la coma para el último track
        
        gj_dtours.append("}]}") # Cerramos el GeoJSON 
        geojson_d = ''.join(gj_dtours)
    else:
        geojson_d = empty_geojson
    
    return geojson_d

def get_polygonized_bidegorris():
    kml_tracks = KML_lstring.objects.all() 
    polys = []

    # Llenamos la lista de bidegorris poligonizados
    for track in kml_tracks:
        polys.append(track.poly)
    
    return polys

# Given a list of geojson strs and a propertiesf {}, adds the properties to the geojson list
def addProperties(geojson, properties):
    props = []
    props.append("\"properties\":{")
    for key in properties:
        props.append("\"" + key + "\":\"" + properties[key] + "\"")
        props.append(",")
    props = props[:-1] # Quitamos la coma para el último property
    props.append("}")
    props_str = ''.join(props)
    geojson.append(props_str)
    return geojson


# def get_multipoint_from_track(gpx):
#     # gpx es una instancia de GPX_track
#     track = GEOSGeometry(gpx.mlstring, srid=4326)
#     track_list_of_points = []
#     # track es una GEOSGeometry
#     for ls in track:
#         for point in ls:
#             p = Point(point)
#             track_list_of_points.append(p)
#     multipoint = MultiPoint(track_list_of_points)
#     return multipoint

# Prueba por si no se puede con MultiPoint el HeatMap
def get_lista_puntos(gpx):
    # gpx es una instancia de GPX_track
    track = GEOSGeometry(gpx.mlstring, srid=4326)
    track_list_of_points = []
    # track es una GEOSGeometry
    for ls in track:
        for point in ls:
            p = Point(point)
            track_list_of_points.append(p)
    return track_list_of_points

# These bunch of functions --> Given a gpx_file from a gpxpy parser, returns a MLSTRING
# From: https://github.com/PetrDlouhy/django-gpxpy/blob/master/django_gpxpy/gpx_parse.py
# Returns points[] from segment
def parse_segment(segment):
    track_list_of_points = []
    for point in segment.points:
        point_in_segment = Point(point.longitude, point.latitude)
        track_list_of_points.append(point_in_segment.coords)
    return track_list_of_points
# Returns multiline, start&end_times from tracks[]
# Método adaptado para coger tiempo inicio y fin 
# TODO que devuelva una lista de data porque son varios tracks los que se pasan
# aunque normalmente solo hay un track en cada gpx
def parse_tracks(tracks):
    data = []
    multiline = []
    for track in tracks:
        start_time, end_time = track.get_time_bounds() 
        for segment in track.segments:
            track_list_of_points = parse_segment(segment)
            if len(track_list_of_points) > 1:
                multiline.append(LineString(track_list_of_points))
    data.append(start_time)
    data.append(end_time)
    data.append(multiline)
    return data
# Returns multiline from routes[]
def parse_routes(routes):
    multiline = []
    for route in routes:
        track_list_of_points = parse_segment(route)
        if len(track_list_of_points) > 1:
            multiline.append(LineString(track_list_of_points))
    return multiline
# Returns track_data[] (data=mlstring + start_time + end_time) from gpx_file
def parse_gpx(track):
    try:
        gpx = gpxpy.parse(track)
        multiline = []
        if gpx.tracks:
            data = parse_tracks(gpx.tracks)
            multiline += data[2]

        if gpx.routes:
            multiline += parse_routes(gpx.routes)
        data[2] = MultiLineString(multiline, srid=4326)
        return data

    except gpxpy.gpx.GPXException as e:
        logger.error("Valid GPX file: %s" % e)
        raise ValidationError(u"Vadný GPX soubor: %s" % e)
# Returns gpx_file from filefield
def parse_gpx_filefield(filefield):
    if filefield.name.endswith(".gz"):
        track_file = gzip.GzipFile(fileobj=filefield).read().decode("utf-8")
    else:
        track_file = filefield.read().decode("utf-8")
    return parse_gpx(track_file)

