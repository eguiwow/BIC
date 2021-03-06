# Cargador de Layers (GPX, KML...)
# From geodjango tutorial = how to load geospatial data with LayerMapping 
# https://docs.djangoproject.com/en/3.1/ref/contrib/gis/tutorial/ - LayerMapping
# cada layer necesita una tabla 
import sys, os
import gpxpy # For manipulating gpx files from python
from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import GEOSGeometry, LineString, WKTWriter
from django.contrib.gis.gdal import DataSource
from .models import GPX_track, GPX_trackpoint , GPX_waypoint, KML_lstring
from .utils import parse_gpx


# # # # # # #
# LOAD GPX  #
# # # # # # #

# Mapear atributos modelo Django contra fields del layer del DataSource 
gpx_track_mapping = {
    'mlstring':'MultiLineString',
}

# Recorre la carpeta datacentre/data/gpx e introduce en la BD los tracks de los GPX 
# hace uso de LayerMapping
# TODO load no solo tracks sino trackpts, wpts, etc.
def load_gpx_lm(verbose=True):
    # LayerMapping --> Docs en https://docs.djangoproject.com/en/3.1/ref/contrib/gis/layermapping/
    dir_gpx_data = Path("/home/eguiwow/github/BIC/bic/datacentre/data/gpx") # Directorio donde están de momento guardados los GPXs
    for filepath in dir_gpx_data.glob( '*.gpx' ):
        print(filepath)
        lm = LayerMapping(GPX_track, str(filepath), gpx_track_mapping, layer=2, transform=False) # Layer = 2 -> Layer = track de un GPX
        lm.save(strict=False, verbose = verbose) # strict = True antes. Esto lo que hace es que si hay un fallo para la ejecución

# Recorre la carpeta datacentre/data/gpx e introduce en la BD los tracks de los GPX 
# Sin usar LayerMapping
# TODO load no solo tracks sino trackpts, wpts, etc.
def load_gpx(verbose=True):
    # gpx may be a track or segment.
    # start_time, end_time = gpx.get_time_bounds()
    dir_gpx_data = Path("/home/eguiwow/github/BIC/bic/datacentre/data/gpx") # Directorio donde están de momento guardados los GPXs
    for filepath in dir_gpx_data.glob( '*.gpx' ):
        print(filepath)
        gpx_file = open(filepath, 'r')
        data = parse_gpx(gpx_file)
        new_track = GPX_track(name=filepath.name, start_time=data[0], end_time=data[1], mlstring=data[2])
        new_track.save()


# # # # # # #
# LOAD KML  #
# # # # # # #

# Dada una feature --> devuelve property
def get_feat_property(feat):
    property = {
        'name': feat.get('Name'),
    }
    return property

# Dada una ruta a un archivo KML --> introduce en la BD los linestrings de los KML 
# https://medium.com/@kitcharoenpoolperm/geodjango-import-data-from-kml-file-de110dba1f60 
def load_kml(verbose=True):
    # Ruta al archivo que queremos introducir en la BD KML_lstrings
    kml_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'kml', 'bidegorris.kml'),)
    # Reading Data by DataSource
    ds = DataSource(kml_file)
    # Writes the Well-Known Text representation of a Geometry.
    wkt_w = WKTWriter()
    # Iterating Over Layers
    for layer in ds:
        for feat in layer:
            if(feat.geom.geom_type.name.startswith('Line')):
                # Get the feature geometry.
                geom = feat.geom

                # get the feature property
                property = get_feat_property(feat)

                if (len(geom.coords) >= 2 ):
                    # Make a GeosGeometry object
                    lstring = GEOSGeometry(wkt_w.write(geom.geos))
                    line = KML_lstring.objects.create(
                        name = property['name'],
                        lstring = lstring,
                        # ST_Buffer() --> Poligonizamos los bidegorris a una anchura de 0.00005
                        poly = lstring.buffer(0.00005,quadsegs=8)                    
                    )
                    print(line)


# # # # #
# MAIN  #
# # # # #

def main():
    load_gpx()
    load_kml()

if __name__ == '__main__':
    main()

