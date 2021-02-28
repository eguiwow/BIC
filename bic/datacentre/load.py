# From geodjango tutorial = how to load geospatial data with LayerMapping 
# https://docs.djangoproject.com/en/3.1/ref/contrib/gis/tutorial/ - LayerMapping
# TODO convertir este load.py en cargador de layers GPX, KML...
# cada layer necesita una tabla 
import sys 
from pathlib import Path
from django.contrib.gis.utils import LayerMapping
<<<<<<< HEAD
from .models import GPX_track, GPX_trackpoint , GPX_waypoint

=======
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

>>>>>>> 35f09649dade736b577ca28ee4f68275cfc79f8d
gpx_track_mapping = {
    'mlstring':'MultiLineString',
}

# world_shp = Path(__file__).resolve().parent / 'data' / 'TM_WORLD_BORDERS-0.3.shp'
<<<<<<< HEAD
#gpx_file_path = Path(__file__).resolve().parent / 'data' / 'gpx' / 'diego.gpx' 
=======
gpx_file_path = Path(__file__).resolve().parent / 'data' / 'gpx' / 'diego.gpx' 
>>>>>>> 35f09649dade736b577ca28ee4f68275cfc79f8d

# Método que recorre la carpeta datacentre/data/gpx e introduce en la BD los tracks de los GPX 
# TODO load no solo tracks sino trackpts, wpts, etc.
def run(verbose=True):
    # LayerMapping --> Docs en https://docs.djangoproject.com/en/3.1/ref/contrib/gis/layermapping/
<<<<<<< HEAD
    dir_gpx_data = Path("/home/eguiwow/github/BIC/bic/datacentre/data/gpx") # Directorio donde están de momento guardados los GPXs
    for filepath in dir_gpx_data.glob( '*.gpx' ):
        print(filepath)
        print(filepath.name)
        lm = LayerMapping(GPX_track, str(filepath), gpx_track_mapping, layer=2, transform=False) # Layer = 2 -> Layer = track de un GPXweb
        lm.save(strict=False, verbose = verbose) # strict = True antes. Esto lo que hace es que si hay un fallo para la ejecución


# Para ejecutar desde terminal sin entrar en el shell del manage.py
def main():
    print("HOLA")
    dir_gpx_data = Path("/home/eguiwow/github/BIC/bic/datacentre/data/gpx")
    for filepath in dir_gpx_data.glob( '*.gpx' ):
        print(filepath)
        print("*******")
        print(filepath.name)

if __name__ == '__main__':
    main()

=======
    # Ejemplo del tutorial:
    # lm = LayerMapping(WorldBorder, str(world_shp), world_mapping, transform=False)
    
    
    lm = LayerMapping(GPX_track, str(gpx_file_path), gpx_track_mapping, layer=2, transform=False)
    lm.save(strict=False, verbose = verbose) # strict = True antes. Esto lo que hace es que si hay un fallo para la ejecución
>>>>>>> 35f09649dade736b577ca28ee4f68275cfc79f8d
