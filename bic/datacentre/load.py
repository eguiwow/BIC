# From geodjango tutorial = how to load geospatial data with LayerMapping 
# TODO convertir este load.py en cargador de layers GPX, KML...
# cada layer necesita una tabla 

from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import WorldBorder

world_mapping = {
    'fips' : 'FIPS',
    'iso2': 'ISO2',
    'iso3' : 'ISO3',
    'un' : 'UN',
    'name' : 'NAME',
    'area' : 'AREA',
    'pop2005' : 'POP2005',
    'region' : 'REGION',
    'subregion' : 'SUBREGION',
    'lon' : 'LON',
    'lat' : 'LAT',
    'mpoly' : 'MULTIPOLYGON',
}

world_shp = Path(__file__).resolve().parent / 'data' / 'TM_WORLD_BORDERS-0.3.shp'

def run(verbose=True):
    lm = LayerMapping(WorldBorder, str(world_shp), world_mapping, transform=False)
    lm.save(strict=True, verbose = verbose)