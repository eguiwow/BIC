#!/bin/bash
# Script para actualizar directamente el map.js de OpenLayers
# 1 - borrar archivos en /home/eguiwow/BIC/ol_mapDjango/dist
$(rm ~/BIC/ol_mapaDjango/HomeMap/dist/*)
# 2 - ejecutar en /home/eguiwow/ol_mapDjango/
cd ~/BIC/ol_mapaDjango/HomeMap && $(npm run build)
$(cd dist)
# 3 - mover archivo que acaba en .js a /home/eguiwow/github/BIC/bic/datacentre/static/js + cambiar nombre
echo "Movido archivo 'map_dev.js' a ~/BIC/bic/datacentre/static/js/ y renombrado a 'map.js'"
cp -f ~/BIC/ol_mapaDjango/HomeMap/dist/*.js ~/BIC/bic/datacentre/static/js/map.js
