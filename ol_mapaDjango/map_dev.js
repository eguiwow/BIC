import 'ol/ol.css';
import {useGeographic, transform, fromLonLat} from 'ol/proj'
import KML from 'ol/format/KML';
import GPX from 'ol/format/GPX';
import Map from 'ol/Map';
import VectorSource from 'ol/source/Vector';
import View from 'ol/View';
import XYZ from 'ol/source/XYZ';
import {Circle as CircleStyle, Fill, Stroke, Style} from 'ol/style';
import {Tile as TileLayer, Vector as VectorLayer} from 'ol/layer';

// Esta función CAMBIA la proyección de Mercator a WGS-84
// TOFIX al cambiar la proyección parece que peta
// useGeographic();

// ###### Variables NO dinámicas ######

// Mapas y servidor de mapas cortesía de... 
var attributions =
  '<a href="https://www.maptiler.com/copyright/" target="_blank">&copy; MapTiler</a> ' +
  '<a href="https://www.openstreetmap.org/copyright" target="_blank">&copy; OpenStreetMap contributors</a>';

// Tiles (pintado del mapa)
var raster = new TileLayer({
  source: new XYZ({
    attributions: attributions,
    // URL correspondiente al servidor mapTiles alojado en el propio PC
    url: 'http://localhost:8080/styles/klokantech-basic/{z}/{x}/{y}.png',
    maxZoom: 20,
  }),
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
var gpx_paths = document.getElementById("paths").innerText.split('#')
// var kml_path = document.getElementById("kml").textContent

// From Zaratamap
var centerLon = JSON.parse(document.getElementById("center").innerText)[0]
var centerLat = JSON.parse(document.getElementById("center").innerText)[1]
var zoom = document.getElementById("zoom").innerText

// Layers tipo KML 
var vector_kml = new VectorLayer({
  source: new VectorSource({
    // url: kml_path,
    url: 'uploads/kml/bidegorris.kml',
    format: new KML(),
  }),
});

// Layers tipo GPX 
var sourceGPX = new VectorSource({
  wrapX: false,
  //TOFIX hay que parsear primero el GPX para pasarlo a JSON
  features: new GPX().readFeatures(gpx_files.innerText)
});

var vector_gpx = new VectorLayer({
  source: sourceGPX,
  style: function (feature) {
    return style[feature.getGeometry().getType()];
  },
});

// Layers tipo GPX con url 
var vector_url = new VectorLayer({
  source: new VectorSource({
    //url: gpx_paths[0],
    url: 'uploads/gpx/diego.gpx',
    format: new GPX(),
  }),
});

// Mapa
var map = new Map({
  layers: [raster, vector_gpx, vector_url, vector_kml],
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
  CenterMap(centerLon, centerLat)
  // Zona DEBUGGING 
  console.log(sourceGPX.getFeatures());
  console.log(sourceGPX.forEachFeature())
  console.log(gpx_files.innerText)
  console.log(kml_path.innerText)
  console.log(kml_path)
});

