# Este fichero busca guardar los archivos KML en la bd.
# En principio los KML van a ser los BIDEGORRIS
# Para hacer un posterior análisis también es necesario hacer un Buffer()
# cada layer necesita una tabla 
import sys, os
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import GEOSGeometry, LineString, WKTWriter
from django.contrib.gis.gdal import DataSource
from .models import KML_lstring


# Mapear atributos modelo Django contra layers del DataSource 
kml_track_mapping = {
    'lstring':'LineString',
}

# Método que dado una ruta a un archivo KML, introduce en la BD los linestrings de los KML 
# https://medium.com/@kitcharoenpoolperm/geodjango-import-data-from-kml-file-de110dba1f60 

def get_feat_property(feat):
       # Get the feature property name.
    property = {
        'name': feat.get('Name'),
    }
    return property

def run(verbose=True):
    # Ruta al archivo que queremos introducir en la BD KML_lstrings
    kml_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'kml', 'bidegorris.kml'),)
    # Reading Data by DataSource
    ds = DataSource(kml_file)
    print(ds)
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
                    line = KML_lstring.objects.create(
                        name = property['name'],
                        # Make a GeosGeometry object
                        lstring = GEOSGeometry(wkt_w.write(geom.geos)),                    
                    )
                    print(line)

# Para ejecutar desde terminal sin entrar en el shell del manage.py
def main():
    print("HOLA")

if __name__ == '__main__':
    main()

