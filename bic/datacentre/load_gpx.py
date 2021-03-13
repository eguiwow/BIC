# From geodjango tutorial = how to load geospatial data with LayerMapping 
# https://docs.djangoproject.com/en/3.1/ref/contrib/gis/tutorial/ - LayerMapping
# TODO convertir este load.py en cargador de layers GPX, KML...
# cada layer necesita una tabla 
import sys 
import gpxpy # For manipulating gpx files from python
from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import GPX_track, GPX_trackpoint , GPX_waypoint
from .utils import parse_gpx

# Mapear atributos modelo Django contra fields del layer del DataSource 
gpx_track_mapping = {
    'mlstring':'MultiLineString',
}

# Método que recorre la carpeta datacentre/data/gpx e introduce en la BD los tracks de los GPX 
# TODO load no solo tracks sino trackpts, wpts, etc.
def run(verbose=True):
    # LayerMapping --> Docs en https://docs.djangoproject.com/en/3.1/ref/contrib/gis/layermapping/
    dir_gpx_data = Path("/home/eguiwow/github/BIC/bic/datacentre/data/gpx") # Directorio donde están de momento guardados los GPXs
    for filepath in dir_gpx_data.glob( '*.gpx' ):
        print(filepath)
        lm = LayerMapping(GPX_track, str(filepath), gpx_track_mapping, layer=2, transform=False) # Layer = 2 -> Layer = track de un GPX
        lm.save(strict=False, verbose = verbose) # strict = True antes. Esto lo que hace es que si hay un fallo para la ejecución

# Método que recorre la carpeta datacentre/data/gpx e introduce en la BD los tracks de los GPX 
# Sin usar LayerMapping
# TODO load no solo tracks sino trackpts, wpts, etc.
def run_no_lm(verbose=True):
    # gpx may be a track or segment.
    # start_time, end_time = gpx_part.get_time_bounds()
    dir_gpx_data = Path("/home/eguiwow/github/BIC/bic/datacentre/data/gpx") # Directorio donde están de momento guardados los GPXs
    for filepath in dir_gpx_data.glob( '*.gpx' ):
        print(filepath)
        gpx_file = open(filepath, 'r')
        data = parse_gpx(gpx_file)
        new_track = GPX_track(name=filepath.name, start_time=data[0], end_time=data[1], mlstring=data[2])
        new_track.save()


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

