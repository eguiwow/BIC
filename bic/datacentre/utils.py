from django.core.exceptions import ValidationError
from django.contrib.gis.geos import GEOSGeometry, LineString, MultiLineString, Point, MultiPoint
from django.contrib.gis.measure import D, Distance
from django.contrib.gis.db.models.functions import Length
from .models import BikeLane, Dtour, Trackpoint
import gpxpy # For manipulating gpx files from python
import geopy.distance
import logging
import datetime


logger = logging.getLogger(__name__)

def empty_geojson():
    """ Devuelve un GeoJSON vacío
  
    Returns
    -------
    formatted_geojson
        GeoJSON vacío con 0 features
    """    
    gj_tracks = []
    gj_tracks.append("{\"type\": \"FeatureCollection\",\"features\": []}")
    formatted_geojson = ''.join(gj_tracks) 
    return formatted_geojson

def tracklist_to_geojson(tracks, geom_name):
    """ Dada una lista de tracks y el nombre de su geometría (geom_name) --> devuelve GeoJSON con esos tracks
    
    Parameters
    ----------
    tracks : <TrackLikeModel>[] (Track, Dtour, BikeLane)
        List of tracklike records from database 
    geom_names:
    mlstring --> MULTILINESTRING
    lstring --> LINESTRING
    poly --> POLYGON
    If tracks is empty --> returns an empty GeoJSON 
    """
    gj_tracks = []
    gj_tracks.append("{\"type\": \"FeatureCollection\",\"features\": [")
    if tracks:
        for track in tracks:
            #Inicio de una Feature
            gj_tracks.append("{\"type\": \"Feature\",\"geometry\": ") 
            #Añadimos a la lista el geojson pertinente
            if geom_name == "bidegorris":
                gj_tracks.append(GEOSGeometry(track.poly, srid=4326).geojson) 
            elif geom_name == "tracks" or geom_name == "dtours":
                if track.mlstring:
                    gj_tracks.append(GEOSGeometry(track.mlstring, srid=4326).geojson) 
                else:
                    gj_tracks.append(GEOSGeometry(track.lstring, srid=4326).geojson) 
            elif geom_name == "bidegorris_lstring":
                gj_tracks.append(GEOSGeometry(track.lstring, srid=4326).geojson)
            elif geom_name == "points":
                del gj_tracks[-1:]
                if not hasattr(track, 'ratio'):
                    if track.device != None:
                        puntos_track = get_trkpts(track)
                    else: 
                        puntos_track = get_lista_puntos(track)
                else:
                    puntos_track = get_lista_puntos(track)
                for punto in puntos_track:
                    gj_tracks.append("{\"type\": \"Feature\",\"geometry\": ") 
                    gj_tracks.append(punto.geojson) # Añadir Point 
                    gj_tracks.append("},")  
                del gj_tracks[-1:]
            else:
                logger.info("ERROR IN PASSING 2nd parameter <geom_name>")
        
            if geom_name != "point":
                # PROPERTIES (length)
                gj_tracks.append(",")  
                length = track.distance
                if geom_name == "tracks": # Si es bidegorri no metemos el tiempo en PROPERTIES
                    timestamp = track.end_time
                    prop_dict = { 'length' : str(length), 'time' : str(timestamp) }
                elif geom_name == "dtours":
                    ratio = track.ratio
                    prop_dict = { 'length' : str(length), 'ratio' : str(ratio) }
                else:
                    prop_dict = { 'length' : str(length) }
                gj_tracks = addProperties(gj_tracks, prop_dict)

            # Cerramos el Feature (track) 
            gj_tracks.append("},")
        
        # Quitamos la coma para el último track
        if len(gj_tracks) > 1:
            gj_tracks = gj_tracks[:-1]
        
        # Cerramos el GeoJSON 
        gj_tracks.append("}]}")
        # Lo unimos en un único String
        formatted_geojson = ''.join(gj_tracks)

    # Si la lista de tracks está vacía, devolvemos un GeoJSON vacío
    else:
        formatted_geojson = empty_geojson()
        logger.info("The tracklist is empty")
    
    return formatted_geojson

def measurements_to_geojson(measurements):
    """ Dada una lista de measurements --> devuelve GeoJSON con esos measurements

    Returns
    -------
    formatted_geojson
        GeoJSON con measurements y properties asociadas
    """    

    gj_measurements = []
    gj_measurements.append("{\"type\": \"FeatureCollection\",\"features\": [")
    if measurements:
        for measurement in measurements:
            #Inicio de una Feature
            gj_measurements.append("{\"type\": \"Feature\",\"geometry\": ") 
            
            #Añadimos a la lista el geojson pertinente
            gj_measurements.append(GEOSGeometry(measurement.point, srid=4326).geojson) 
            # PROPERTIES ()
            gj_measurements.append(",")  
            value = measurement.value
            units = measurement.sensor.units
            timestamp = measurement.time 
            vel = measurement.trkpoint.velocity
            prop_dict = { 'value' : str(value), 'units' : units, 'time' : str(timestamp), 'velocity' : str(vel) }
            gj_measurements = addProperties(gj_measurements, prop_dict)

            # Cerramos el Feature (track) 
            gj_measurements.append("},")
        
        # Quitamos la coma para el último track
        if len(gj_measurements) > 1:
            gj_measurements = gj_measurements[:-1]
        
        # Cerramos el GeoJSON 
        gj_measurements.append("}]}")
        # Lo unimos en un único String
        formatted_geojson = ''.join(gj_measurements)

    # Si la lista de tracks está vacía, devolvemos un GeoJSON vacío
    else:
        formatted_geojson = empty_geojson()
        logger.info("The tracklist is empty")
    
    return formatted_geojson    

def points_vel_to_geojson(trkpoints):
    """ Dada una lista de trkpoints --> devuelve GeoJSON con trkpoints y su velocidad

    Returns
    -------
    formatted_geojson
        GeoJSON con trkpoints y velocidad asociada
    """    

    gj_trkpoints = []
    gj_trkpoints.append("{\"type\": \"FeatureCollection\",\"features\": [")
    if trkpoints:
        for point in trkpoints:
            #Inicio de una Feature
            gj_trkpoints.append("{\"type\": \"Feature\",\"geometry\": ") 
            
            #Añadimos a la lista el geojson pertinente
            gj_trkpoints.append(GEOSGeometry(point.point, srid=4326).geojson) 
            # PROPERTIES ()
            gj_trkpoints.append(",")  
            value = point.velocity
            units = "km/h"
            timestamp = point.time 
            prop_dict = { 'value' : str(value), 'units' : units, 'time' : str(timestamp) }
            gj_trkpoints = addProperties(gj_trkpoints, prop_dict)

            # Cerramos el Feature (track) 
            gj_trkpoints.append("},")
        
        # Quitamos la coma para el último track
        if len(gj_trkpoints) > 1:
            gj_trkpoints = gj_trkpoints[:-1]
        
        # Cerramos el GeoJSON 
        gj_trkpoints.append("}]}")
        # Lo unimos en un único String
        formatted_geojson = ''.join(gj_trkpoints)

    # Si la lista de tracks está vacía, devolvemos un GeoJSON vacío
    else:
        formatted_geojson = empty_geojson()
        logger.info("The tracklist is empty")
    
    return formatted_geojson    



def get_dtours(tracks, polys):
    """ Dada una lista de tracks y de bidegorris (polys) --> devuelve multilinestring[] con properties[dtour_length, ratio dtour/track]

    Applies ST_Difference() between a list of tracks and polys (diff = track - poly [mlstring])

    Parameters
    ----------
    tracks : <TrackLikeModel>[] (Track, Dtour, BikeLane)
        Lista de elementos tipo track de la base de datos
    polys : MultiPolygon[]
        Lista de polígonos representando los carriles bici

    Returns
    -------
    geojson_d
        GeoJSON con los dtours y sus properties asociadas
    """
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
                
                # PROPERTIES
                # Calcular distancia dtours
                dtour.transform(3035)
                dtour_length = 0
                for lstring in dtour:
                    dtour_length += lstring.length
                ratio_dtour_to_track = (dtour_length/track_length)*100
                
                prop_dict = { 'length' : str(dtour_length), 'ratio' : str(ratio_dtour_to_track) }
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
    """ Devuelve los bidegorris en forma de polígono

    Returns
    -------
    polys :
        Lista de polígonos representando los carriles bici
    """
    
    kml_tracks = BikeLane.objects.all() 
    polys = []

    # Llenamos la lista de bidegorris poligonizados
    for track in kml_tracks:
        polys.append(track.poly)
    
    return polys

def get_trkpts(track):
    """ Dada una lista de tracks y de bidegorris (polys) --> devuelve multilinestring[] con properties[dtour_length, ratio dtour/track]

    Applies ST_Difference() between a list of tracks and polys (diff = track - poly [mlstring])

    Parameters
    ----------
    track : Track
        Track del que sacar los trackpoints

    Returns
    -------
    lista_puntos :
        lista con trackpoints de ese track
    """

    lista_puntos = []
    trackpoints = Trackpoint.objects.filter(track=track)
    for trackpoint in trackpoints:
        lista_puntos.append(trackpoint.point)
    return lista_puntos

# Given a list of geojson strs and a properties {}, adds the properties to the geojson list
def addProperties(geojson, properties):
    """ Dado un geojson --> añade properties

    Parameters
    ----------
    geojson : 
        geojson al que queremos añadir las properties
    properties : 
        lista de properties

    Returns
    -------
    geojson
        GeoJSON con los properties ya asociados
    """

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

# Given a list of polys, a mlstring and , new_track --> calc dtours from that track
def calc_dtours(polys, geom, new_track):
    """ Dados los bidegorris y una geometría, calcula los desvíos respecto de los bidegorris y los guarda en la BD

    Parameters
    ----------
    geom : <TrackLikeModel>[] (Track, Dtour, BikeLane)
        La geometría del track 
    polys : MultiPolygon[]
        Lista de polígonos representando los carriles bici
    new_track :
        track que se acaba de añadir

s    """

    track_length = geom.length
    geom.transform(4326)
    intersected = False
    if polys:
        for i in polys: # sacamos cada poly de la lista
            if geom.intersects(i):# if they intersect --> then do the .difference()
                intersected = True
                geom = geom.difference(i) # Guardamos el resultante como nuevo track y guardamos solo al final
        if intersected:                
            dtour = geom # Difference = Track - Poly                
            dtour.transform(3035)
            dtour_length = 0
            for lstring in dtour:
                dtour_length += lstring.length
            ratio_dtour_to_track = (dtour_length/track_length)*100
            dtour = Dtour(track= new_track, mlstring = dtour, distance=dtour_length, ratio=ratio_dtour_to_track).save()
            pr_update = "Uploading DTOURs associated to..." + str(new_track)
            logger.info(pr_update)
            intersected = False

# Devuelve lista_puntos partiendo de un track
def get_lista_puntos(track):
    """ Dado un track devuelve los puntos de ese track

    Parameters
    ----------
    track : 
        track del que se extraen los puntos

    Returns
    -------
    ml_list_of_points
        lista de puntos
    """
    # track tiene un atributo .mlstring
    GEOStrack = GEOSGeometry(track.mlstring, srid=4326)
    ml_list_of_points = []
    # track es una GEOSGeometry
    for ls in GEOStrack:
        for point in ls:
            p = Point(point)
            ml_list_of_points.append(p)
    return ml_list_of_points

def calc_distance_between_2_points(point1, point2):
    """0 Calcula distancia entre 2 puntos

    Parameters
    ----------
    point1 & point2: 
        puntos entre los que calcular distancia

    Returns
    -------
    distancia entre puntos en km    
    """

    # distance in m
    
    coords_1 = (point1[0], point1[1])
    coords_2 = (point2[0], point2[1])

    return geopy.distance.geodesic(coords_1, coords_2).km

def calc_velocity_between_2_points(point1, point2, time1, time2):
    """ Devuelve la velocidad entre 2 puntos 

    Parameters
    ----------
    point1 & point2 : 
        puntos entre los que calcular velocidad
    time1 & time2 : 
        timestamps de los puntos

    Returns
    -------
    velocidad en km/h
    """

    # vel = space / time
    # time (s):
    diff_secs = abs(time2-time1)
    passed_time = diff_secs.total_seconds()
    # space (km):
    distance_between_points = calc_distance_between_2_points(point1, point2)
    # vel (km/h):
    velocity = distance_between_points/(passed_time/3600)
    if velocity > 40: # si la velocidad es mayor a 40km/h es con toda probabilidad un error 
        velocity = -1 
    return velocity

# These bunch of functions --> Given a gpx_file from a gpxpy parser, returns a MLSTRING
# From: https://github.com/PetrDlouhy/django-gpxpy/blob/master/django_gpxpy/gpx_parse.py
# Returns points[] from segment
def parse_segment(segment):
    ml_list_of_points = []
    track_list_of_points = []
    for point in segment.points:
        point_in_segment = Point(point.longitude, point.latitude)
        ml_list_of_points.append(point_in_segment.coords)
        track_list_of_points.append([point_in_segment, point.time])
    data = [ml_list_of_points, track_list_of_points]
    return data
# Returns multiline, start&end_times from tracks[]
# Método adaptado para coger tiempo inicio y fin 
# Aunque normalmente solo hay un track en cada gpx, en caso de que hubiera más habría que modificar este método
# devolviendo una lista de data
def parse_tracks(tracks):
    data = []
    multiline = []
    for track in tracks:
        start_time, end_time = track.get_time_bounds() 
        for segment in track.segments:
            lists_points = parse_segment(segment)
            ml_list_of_points = lists_points[0]
            if len(ml_list_of_points) > 1:
                multiline.append(LineString(ml_list_of_points))
    data.append(start_time)
    data.append(end_time)
    data.append(multiline)
    data.append(lists_points[1])
    return data
# Returns multiline from routes[]
def parse_routes(routes): # TODO está sin probar => subir GPX con codificación route para probar
    multiline = []
    for route in routes:
        lists_points = parse_segment(route)
        ml_list_of_points = lists_points[0]
        if len(ml_list_of_points) > 1:
            multiline.append(LineString(ml_list_of_points))
    data = [multiline, lists_points[1]]        
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
            routes = parse_routes(gpx.routes)
            multiline += routes[0]
            data[3] = routes[1]
        data[2] = MultiLineString(multiline, srid=4326)
        return data

    except gpxpy.gpx.GPXException as e:
        logger.error("Valid GPX file: %s" % e) 
        raise ValidationError(u"Valid GPX file: %s" % e)

