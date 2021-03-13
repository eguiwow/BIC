from django.contrib.gis.geos import GEOSGeometry # For lazy geometries
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import LineString, MultiLineString, Point
import gpxpy

# Returns an empty but formatted GeoJSON
def empty_geojson():
    gj_tracks = []
    gj_tracks.append("{\"type\": \"FeatureCollection\",\"features\": []}")
    formatted_geojson = ''.join(gj_tracks) 
    return formatted_geojson

# Given a list of tracks returns a formatted GeoJSON containing those tracks [MULTILINESTRING] !
# TODO devolver empty_geojson si tracks está vacío
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
    
    # Quitamos la coma para el último track
    if len(gj_tracks) > 1:
        gj_tracks = gj_tracks[:-1]
        gj_tracks.append("}")

    gj_tracks.append("]}") # Cerramos el GeoJSON 
    formatted_geojson = ''.join(gj_tracks)
    
    return formatted_geojson

# These bunch of functions --> Given a gpx_file from a gpxpy parser, returns a MLSTRING
# From: https://github.com/PetrDlouhy/django-gpxpy/blob/master/django_gpxpy/gpx_parse.py
def parse_segment(segment):
    track_list_of_points = []
    for point in segment.points:
        point_in_segment = Point(point.longitude, point.latitude)
        track_list_of_points.append(point_in_segment.coords)
    return track_list_of_points

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

def parse_routes(routes):
    multiline = []
    for route in routes:
        track_list_of_points = parse_segment(route)
        if len(track_list_of_points) > 1:
            multiline.append(LineString(track_list_of_points))
    return multiline

def parse_gpx(track):
    try:
        gpx = gpxpy.parse(track)
        multiline = []
        if gpx.tracks:
            data = parse_tracks(gpx.tracks)
            multiline += data[2]

        if gpx.routes:
            multiline += parse_routes(gpx.routes)
        data[2] = MultiLineString(multiline)
        return data

    except gpxpy.gpx.GPXException as e:
        logger.error("Valid GPX file: %s" % e)
        raise ValidationError(u"Vadný GPX soubor: %s" % e)

def parse_gpx_filefield(filefield):
    if filefield.name.endswith(".gz"):
        track_file = gzip.GzipFile(fileobj=filefield).read().decode("utf-8")
    else:
        track_file = filefield.read().decode("utf-8")
    return parse_gpx(track_file)

