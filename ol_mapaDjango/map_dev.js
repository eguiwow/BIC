import 'ol/ol.css';
import {KML, GPX, GeoJSON} from 'ol/format';
import Map from 'ol/Map';
import VectorSource from 'ol/source/Vector';

import Feature from 'ol/Feature';
import Circle from 'ol/geom/Circle';

import {XYZ, OSM} from 'ol/source';
import View from 'ol/View';
import {Circle as CircleStyle, Fill, Stroke, Style} from 'ol/style';
import {Tile as TileLayer, Vector as VectorLayer, Group as LayerGroup} from 'ol/layer';
import LayerSwitcher from 'ol-layerswitcher';
import {useGeographic, transform, fromLonLat} from 'ol/proj'
import {getAllTextContent, parse} from 'ol/xml';

// Pequeña intro sobre Proyecciones en OpenLayers
// ----------------------------------------------
// OpenLayers trabaja por defecto con proyección EPSG:3857 (Mercator)
// Nuestros datos (coordenadas lon;lat) están en proyección EPSG:4326 (WGS-84)
// Tenemos que hacer la conversión en la vista (View)
// Si nuestro mapa base (TileLayer) está en proyección Mercator se ajustará en función del cambio que se haga
// Hay veces que al introducir una Feature puede no mostrarse. Puede tener que ver con su proyección

// TODO (Revisar qué hace la función) Esta función CAMBIA la proyección de Mercator (EPSG:3857) --> WGS-84
// useGeographic();

// ###### Variables NO dinámicas ######

// Mapas y servidor de mapas cortesía de... 
var attributions =
  '<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> ' +
  '<a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>';

// TODO - reactivar server de OpenMapTiles
// var openmap_tiles = new TileLayer({
//   source: new XYZ({
//     attributions: attributions,
//     //URL correspondiente al servidor de mapas alojado en este mismo servidor
//     url: 'http://localhost:8080/styles/klokantech-basic/{z}/{x}/{y}.png',
//     maxZoom: 20,
//   }),
// });

var osm_tiles = new TileLayer({
  type: 'base',
  source: new OSM(),
});

// ###### Estilo de pintado de Features ######
// TODO: customizarlo al gusto
var style = {
  'Point': new Style({
    image: new CircleStyle({
      fill: new Fill({
        color: 'rgba(255,255,0,0.4)',
      }),
      radius: 5,
      stroke: new Stroke({
        color: '#ff0', 
        width: 1,
      }),
    }),
  }),
  'LineString': new Style({
    stroke: new Stroke({
      color: '#000', // BLACK
      width: 3,
    }),
  }),
  'MultiLineString': new Style({
    stroke: new Stroke({
      color: '#0f0', // GREEN
      width: 3,
    }),
  }),
  'Polygon': new Style({
    stroke: new Stroke({
      color: 'blue',
      lineDash: [4],
      width: 3,
    }),
    fill: new Fill({
      color: 'rgba(0, 0, 255, 0.1)',
    }),
  }),
};
var style2 = {
  'LineString': new Style({
    stroke: new Stroke({
      color: '#fff', //WHITE
      width: 3,
    }),
  }),
  'MultiLineString': new Style({
    stroke: new Stroke({
      color: '#f00', //RED
      width: 3,
    }),
  }),
};

// Función para llamar en VectorSource que aplica el estilo definido en 'style'
var styleFunction = function (feature) {
  return style[feature.getGeometry().getType()];
};
// Estilo 2 TODO mejorar para otro tipo de tracks
var styleFunction2 = function(feature){
  return style2[feature.getGeometry().getType()];
};

// ###### FIN Estilo de pintado de Features ######


// ###### Variables dinámicas ######
// var gpx_files = document.getElementById("gpx_files")
var json_tracks = document.getElementById("json_tracks")
var json_dtours = document.getElementById("json_dtours")
var json_bufflines = document.getElementById("json_bufflines")
var geojson_tracks = new GeoJSON().readFeatures(JSON.parse(json_tracks.innerText))
var geojson_dtours = new GeoJSON().readFeatures(JSON.parse(json_dtours.innerText))
var buffered_lines = new GeoJSON().readFeatures(JSON.parse(json_bufflines.innerText))
var botonDebug = document.getElementById("debugButton")
var botonCenter = document.getElementById("centerButton")
// From Zaratamap
var centerLon = JSON.parse(document.getElementById("center").innerText)[0]
var centerLat = JSON.parse(document.getElementById("center").innerText)[1]
var zoom = document.getElementById("zoom").innerText
// ###### FIN Variables dinámicas ######

// ###### Layers tipo JSON ######
var sourceJSON = new VectorSource({
  wrapX: false,
  features: geojson_tracks
});
var sourceJSONdtour = new VectorSource({
  wrapX: false,
  features: geojson_dtours
});
var sourceJbufflines = new VectorSource({
  wrapX:false,
  features: buffered_lines
});

var vectorJSON = new VectorLayer({
  title: 'tracks',
  source: sourceJSON,
  style: styleFunction,
});
var vectorJSONdtour = new VectorLayer({
  title: 'dtours',
  source: sourceJSONdtour,
  style: styleFunction2,
});
var vectorJbufflines = new VectorLayer({
  title: 'bidegorris',
  source: sourceJbufflines,
  style: styleFunction,
});
// ###### FIN Layers tipo JSON ######

// ###### Layers tipo KML ######
// TODO - probar bidegorris.kml desde url de Bizkaia 
// --> VectorSource()
// ###### FIN Layers tipo KML ######

// ###### Layers tipo GPX ######
// var sourceGPX = new VectorSource({
//   url: 'diego.gpx',
//   format: new GPX(),
// });

// var vector_gpx = new VectorLayer({
//   source: sourceGPX,
//     style: styleFunction,
// });
// ###### FIN Layers tipo GPX ######

// Grupo de Layers para LayerSwitcher
var overlayGroup = new LayerGroup({
  title: 'Capas',
  layers: [vectorJSON, vectorJSONdtour, vectorJbufflines],
})
// LayerSwitcher (para cambiar entre capas)
var layerSwitcher = new LayerSwitcher();

// Mapa
var map = new Map({
  layers: [osm_tiles, overlayGroup], // Capas de información geoespacial
  target: document.getElementById('map'), // Elemento HTML donde va situado el mapa
  view: new View({ // Configuración de la vista (centro, proyección del mapa)
    // Esta función comentada es para cuando la proyección usada sea Mercator
    // center: fromLonLat([centerLon, centerLat]),
    center: [centerLon,centerLat],
    projection: 'EPSG:4326',
    // https://stackoverflow.com/questions/58107691/openlayers-map-center-issue
    zoom: zoom,
  }),
});
// Añadimos LayerSwitcher
map.addControl(layerSwitcher);

// ###### Funciones ######
// Display Feature Info --> example OpenLayers 
// TODO - esta función será la que tendrá que sacar información de los puntos de las rutas
var displayFeatureInfo = function (pixel) {
  var features = [];
  map.forEachFeatureAtPixel(pixel, function (feature) {
    features.push(feature);
  });
  if (features.length > 0) {
    var info = [];
    var i, ii;
    for (i = 0, ii = features.length; i < ii; ++i) {
      info.push(features[i].get('name'));
    }
    document.getElementById('info').innerHTML = info.join(', ') || '(unknown)';
    map.getTarget().style.cursor = 'pointer';
  } else {
    document.getElementById('info').innerHTML = '&nbsp;';
    map.getTarget().style.cursor = '';
  }
  var loc = window.location.pathname;
  console.log(loc);
};

// Centrar Mapa 
// src: https://gis.stackexchange.com/questions/112892/change-openlayers-3-view-center
function CenterMap(long, lati) {
  // console.log("Long: " + long + " Lat: " + lati);
  // map.getView().setCenter(fromLonLat([long, lati]));
  map.getView().setCenter([long, lati]);
  map.getView().setZoom(13);
}

// ###### FIN Funciones ######

// ###### EVENTOS del mapa ######
// Drag
map.on('pointermove', function (evt) {
  if (evt.dragging) {
    return;
  }
  // var pixel = map.getEventPixel(evt.originalEvent);
  // displayFeatureInfo(pixel);
});

// Click
map.on('click', function (evt) {
  // displayFeatureInfo(evt.pixel);
  

});
// ###### FIN EVENTOS del mapa ######

// ###### BOTONES ######
botonDebug.onclick = function(){
// Zona DEBUGGING
  console.log("HOLA");
  console.log(json_bufflines)
};

botonCenter.onclick = function(){
  // Centramos mapa
  CenterMap(centerLon, centerLat);
};
  

// ###### FIN BOTONES ######