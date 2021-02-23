# From geodjango tutorial = how to load geospatial data with LayerMapping 
# TODO convertir este load.py en cargador de layers GPX, KML...
# cada layer necesita una tabla 

from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import GPX_track, GPX_trackpoint , GPX_waypoint #WorldBorder

# world_mapping = {
#     'fips' : 'FIPS',
#     'iso2': 'ISO2',
#     'iso3' : 'ISO3',
#     'un' : 'UN',
#     'name' : 'NAME',
#     'area' : 'AREA',
#     'pop2005' : 'POP2005',
#     'region' : 'REGION',
#     'subregion' : 'SUBREGION',
#     'lon' : 'LON',
#     'lat' : 'LAT',
#     'mpoly' : 'MULTIPOLYGON',
# }

gpx_track_mapping = {
    'mlstring':'MultiLineString',
}

# world_shp = Path(__file__).resolve().parent / 'data' / 'TM_WORLD_BORDERS-0.3.shp'
gpx_file_path = Path(__file__).resolve().parent / 'data' / 'gpx' / 'diego.gpx' 

def run(verbose=True):
    # LayerMapping --> Docs en https://docs.djangoproject.com/en/3.1/ref/contrib/gis/layermapping/
    # Ejemplo del tutorial:
    # lm = LayerMapping(WorldBorder, str(world_shp), world_mapping, transform=False)
    
    
    lm = LayerMapping(GPX_track, str(gpx_file_path), gpx_track_mapping, layer=2, transform=False)
    lm.save(strict=False, verbose = verbose) # strict = True antes. Esto lo que hace es que si hay un fallo para la ejecución