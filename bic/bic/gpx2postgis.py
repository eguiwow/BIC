# From https://gis.stackexchange.com/questions/52271/automating-batch-load-of-multiple-gpx-files-into-postgis

import os
from osgeo import ogr
from glob import glob

# Establish a connection to a PostGIS database
pg = ogr.GetDriverByName('PostgreSQL')
if pg is None:
    raise RuntimeError('PostgreSQL driver not available')
conn = pg.Open("PG:dbname='bic_db' user='eguiwow'", True)
if conn is None:
    raise RuntimeError('Cannot open dataset connection')

# Loop through each GPX file
for gpx_file in glob('/home/eguiwow/github/BIC/bic/datacentre/data/gpx/*.gpx'):
    ds = ogr.Open(gpx_file)
    if ds is None:
        print('Skipping ' + gpx_file)
    print('Opened ' + gpx_file)
    prefix = os.path.splitext(os.path.basename(gpx_file))[0]
    # Get each layer
    for iLayer in range(ds.GetLayerCount()):
        layer = ds.GetLayer(iLayer)
        layer_name = prefix + '_' + layer.GetName()
        if layer.GetFeatureCount() == 0:
            print(' -> Skipping ' + layer_name + ' since it is empty')
        else:
            print(' -> Copying ' + layer_name)
            pg_layer = conn.CopyLayer(layer, layer_name)
            if pg_layer is None:
                print(' |-> Failed to copy')