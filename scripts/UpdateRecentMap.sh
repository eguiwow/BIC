#!/bin/bash
# Script para actualizar directamente el recent_map.js de OpenLayers
# 1 - borrar archivos en /home/eguiwow/BIC/ol_mapDjango/dist
$(rm ~/BIC/ol_mapaDjango/RecentMap/dist/*)
# 2 - ejecutar en /home/eguiwow/ol_mapaDjango/
cd ~/BIC/ol_mapaDjango/RecentMap && $(npm run build)
$(cd dist)
# 3 - mover archivo que acaba en .js a /home/eguiwow/BIC/bic/datacentre/static/js + cambiar nombre
echo "Movido archivo 'map_dev.js' a ~/BIC/bic/datacentre/static/js/ y renombrado a 'recent_map.js'"
cp -f ~/BIC/ol_mapaDjango/RecentMap/dist/*.js ~/BIC/bic/datacentre/static/js/recent_map.js
