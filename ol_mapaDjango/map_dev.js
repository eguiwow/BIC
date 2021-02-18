import 'ol/ol.css';
import {KML, GPX, GeoJSON} from 'ol/format';
import Map from 'ol/Map';
import VectorSource from 'ol/source/Vector';
import {XYZ, OSM} from 'ol/source';
import View from 'ol/View';
import {Circle as CircleStyle, Fill, Stroke, Style} from 'ol/style';
import {Tile as TileLayer, Vector as VectorLayer} from 'ol/layer';
import {useGeographic, transform, fromLonLat} from 'ol/proj'
import {getAllTextContent, parse} from 'ol/xml';

// Esta función CAMBIA la proyección de Mercator a WGS-84
// TOFIX al cambiar la proyección parece que peta
// useGeographic();

// ###### Variables NO dinámicas ######

// Mapas y servidor de mapas cortesía de... 
var attributions =
  '<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> ' +
  '<a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>';

// TOFIX - server de OpenMapTiles
// var raster = new TileLayer({
//   source: new XYZ({
//     attributions: attributions,
//     //URL correspondiente al servidor de mapas alojado en este mismo servidor
//     url: 'http://localhost:8080/styles/klokantech-basic/{z}/{x}/{y}.png',
//     maxZoom: 20,
//   }),
// });

var raster = new TileLayer({
  source: new OSM(),
});


// Estilo de pintado de círculos/líneas/etc. 
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
      color: '#f00',
      width: 3,
    }),
  }),
  'MultiLineString': new Style({
    stroke: new Stroke({
      color: '#0f0',
      width: 3,
    }),
  }),
};

// ###### Variables dinámicas ######
var gpx_files = document.getElementById("gpx_files")
var json_files = document.getElementById("json_files")

// From Zaratamap
var centerLon = JSON.parse(document.getElementById("center").innerText)[0]
var centerLat = JSON.parse(document.getElementById("center").innerText)[1]
var zoom = document.getElementById("zoom").innerText

var xml_doc = parse(gpx_files.innerText)

// Layers tipo JSON
// var sourceJSON = new VectorSource({
//   wrapX: false,
//   features: new GeoJSON().readFeatures(JSON.parse(json_files))
// });

// var vectorJSON = new VectorLayer({
//   source: sourceJSON,
// });

// Layers tipo KML 
// --> VectorSource()

// Layers tipo GPX 

// var sourceGPX = new VectorSource({
//   wrapX: false,
//   //TOFIX hay que parsear primero el GPX para pasarlo a JSON
//   features: new GPX().readFeatures(gpx_files.innerText)
// });

// var vector_gpx = new VectorLayer({
//   source: xml_doc,
//   style: function (feature) {
//     return style[feature.getGeometry().getType()];
//   },
// });

var sourceGPX = new VectorSource({
  url: 'diego.gpx',
  //URL.createObjectURL(xml_doc),
  format: new GPX(),
});


var vector_gpx2 = new VectorLayer({
  source: sourceGPX,
    style: function (feature) {
    return style[feature.getGeometry().getType()];
  },

});

// Mapa
var map = new Map({
  layers: [raster, vector_gpx2],
  target: document.getElementById('map'),
  view: new View({
    // Esta función comentada no cambia la proyección pero nos permite fijar el centro con lonlat
    center: fromLonLat([centerLon, centerLat]),
    // center: [centerLon,centerLat],
    // projection: 'EPSG:4326',
    // https://stackoverflow.com/questions/58107691/openlayers-map-center-issue
    zoom: zoom,
  }),
});

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

// Funciones
// Centrar Mapa https://gis.stackexchange.com/questions/112892/change-openlayers-3-view-center
function CenterMap(long, lati) {
  console.log("Long: " + long + " Lat: " + lati);
  map.getView().setCenter(fromLonLat([long, lati]));
  map.getView().setZoom(13);
}

// EVENTOS del mapa
// Drag
map.on('pointermove', function (evt) {
  if (evt.dragging) {
    return;
  }
  var pixel = map.getEventPixel(evt.originalEvent);
  displayFeatureInfo(pixel);
});
// Click
map.on('click', function (evt) {
  displayFeatureInfo(evt.pixel);
  // Centramos mapa
  // TODO que esta llamada a CenterMap() esté en un botón a parte
  CenterMap(centerLon, centerLat);
  // Zona DEBUGGING 
  console.log(json_files).getGeommetry();
  console.log(json.files);

});

