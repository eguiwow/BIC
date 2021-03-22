// **********************************
//           MAPA CONSULTA
// **********************************
import 'ol/ol.css';
import {KML, GPX, GeoJSON} from 'ol/format';
import Map from 'ol/Map';
import VectorSource from 'ol/source/Vector';
import {XYZ, OSM, Stamen} from 'ol/source';
import View from 'ol/View';
import {Circle as CircleStyle, Fill, Stroke, Style} from 'ol/style';
import {Tile as TileLayer, Vector as VectorLayer, Group as LayerGroup, Heatmap as HeatMapLayer} from 'ol/layer';
import LayerSwitcher from 'ol-layerswitcher';
import Draw, {createBox} from 'ol/interaction/Draw';

import Feature from 'ol/Feature';
import {useGeographic, transform, fromLonLat, toLonLat} from 'ol/proj'
import {getAllTextContent, parse} from 'ol/xml';
import { add } from 'ol/coordinate';

// Pequeña intro sobre Proyecciones en OpenLayers
// ----------------------------------------------
// OpenLayers trabaja por defecto con proyección EPSG:3857 (Mercator)
// Nuestros datos (coordenadas lon;lat) están en proyección EPSG:4326 (WGS-84)
// Tenemos que hacer la conversión en la vista (View)
// Si nuestro mapa base (TileLayer) está en proyección Mercator se ajustará en función del cambio que se haga
// Hay veces que al introducir una Feature puede no mostrarse. Puede tener que ver con su proyección

// [EN DUDA] Esta función CAMBIA la proyección de Mercator (EPSG:3857) --> WGS-84
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
//
// Tiles de Stamen
// var raster = new TileLayer({
//   source: new Stamen({
//     layer: 'toner',
//   }),
// });


// Tiles de OpenStreetMaps
var osm_tiles = new TileLayer({
  type: 'base', // Indicamos que es mapa base para el LayerSwitcher 
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
  'MultiPoint': new Style({
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
// TODO mejorar para otro tipo de tracks
var styleFunction2 = function(feature){
  return style2[feature.getGeometry().getType()];
};

// ###### FIN Estilo de pintado de Features ######


// ###### Variables dinámicas ######
var json_tracks = document.getElementById("json_tracks")
var json_dtours = document.getElementById("json_dtours")
var json_bidegorris = document.getElementById("json_bidegorris")
var gj_tracks = new GeoJSON().readFeatures(JSON.parse(json_tracks.innerText))
var gj_dtours = new GeoJSON().readFeatures(JSON.parse(json_dtours.innerText))
var gj_bidegorris = new GeoJSON().readFeatures(JSON.parse(json_bidegorris.innerText))
// Botones
var botonDebug = document.getElementById("debugButton")
var botonCenter = document.getElementById("centerButton")
var botonSelectArea = document.getElementById("selectAreaButton")
// BBox boundaries form
var ne_lon = document.getElementById("id_NE_lon").value;
var ne_lat = document.getElementById("id_NE_lat").value;
var sw_lon = document.getElementById("id_SW_lon").value;
var sw_lat = document.getElementById("id_SW_lat").value;
var consulta_vacia = document.getElementById("consulta_vacia");
var lon1, lon2, lat1, lat2;
// Center & Zoom [From Zaratamap]
var centerLon = JSON.parse(document.getElementById("center").innerText)[0]
var centerLat = JSON.parse(document.getElementById("center").innerText)[1]
var zoom = document.getElementById("zoom").innerText
// ###### FIN Variables dinámicas ######

// ###### Layers tipo JSON ######
var sourceGJTracks = new VectorSource({
  wrapX: false,
  features: gj_tracks
});
var sourceGJDtours = new VectorSource({
  wrapX: false,
  features: gj_dtours
});
var sourceGJBidegorris = new VectorSource({
  wrapX:false,
  features: gj_bidegorris
});

var vTracks = new VectorLayer({
  title: 'tracks',
  visible: true,
  source: sourceGJTracks,
  style: styleFunction,
});
var vDtours = new VectorLayer({
  title: 'dtours',
  source: sourceGJDtours,
  visible: false,
  style: styleFunction2,
});
var vBidegorris = new VectorLayer({
  title: 'bidegorris',
  visible: false,
  source: sourceGJBidegorris,
  style: styleFunction,
});

// Capa para Draw
var srcDraw = new VectorSource({wrapX: false});
var vDraw = new VectorLayer({source: srcDraw,});

// Número de tracks
var tracksLength = vTracks.getSource().getFeatures().length;

// Grupo de Layers para LayerSwitcher
var grupoVectores = new LayerGroup({
  title: 'Capas',
  layers: [vTracks, vDtours, vBidegorris],
})
// LayerSwitcher (para cambiar entre capas) - https://github.com/walkermatt/ol-layerswitcher 
var layerSwitcher = new LayerSwitcher();
var typeSelect = 'None';
// Mapa
var map = new Map({
  layers: [osm_tiles, grupoVectores, vDraw], // Capas de información geoespacial
  target: document.getElementById('map'), // Elemento HTML donde va situado el mapa
  view: new View({ // Configuración de la vista (centro, proyección del mapa)
    // Esta función es para cuando la proyección usada sea Mercator
    // center: fromLonLat([centerLon, centerLat]),
    center: [centerLon,centerLat],
    projection: 'EPSG:4326',
    // https://stackoverflow.com/questions/58107691/openlayers-map-center-issue
    zoom: zoom,
  }),
});
// Añadimos LayerSwitcher
map.addControl(layerSwitcher);





// DIBUJAR BBOX - https://openlayers.org/en/latest/examples/draw-shapes.html?q=draw
// Adaptado para dibujar solo Box

var draw; // global so we can remove it later
function addInteraction() {
  // Si no tenemos "Selección Área" no hacemos ná
  // draw.removeLastPoint();
  var value = typeSelect;
  console.log(value);
  if (value != 'None') {
    var geometryFunction;
    if (value == 'Box') {
      value = 'Circle';
      geometryFunction = createBox();
    }
    draw = new Draw({
      source: srcDraw,
      type: value,
      geometryFunction: geometryFunction,
    });
    map.addInteraction(draw);
  }
}
// FIN DIBUJAR BBOX





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

// ###### EVENTOS ######
// OnLoad(document) --> document.onload se hace antes que window.onload
document.onload = function(){

}
// OnLoad (window)
window.onload = function() {
  // Si la consulta es vacía --> sacamos alerta 
  if (consulta_vacia.innerText == 1){
    alert("No existe actividad en este rango, prueba a cambiar el rango temporal o espacial")
  }
};

// EVENTOSmapa 
// Drag
map.on('pointermove', function (evt) {
  if (evt.dragging) {
    return;
  }
  // var pixel = map.getEventPixel(evt.originalEvent);
  // displayFeatureInfo(pixel);
});

var primerclick = true;
// Click
map.on('click', function (evt) {  
  // evt.coordinate guarda las coordenadas del evento de click
  // TODO - cambiar dónde se recoge las coordenadas, debería de hacerse en una función aparte yo creo
  if (typeSelect == 'Box'){
    if (primerclick == true){ // Primer click --> borramos y empezamos BBox
      if (draw) srcDraw.clear()
      lon1 = evt.coordinate[0];
      lat1 = evt.coordinate[1];
      primerclick = false;
    }else{ // Segundo click --> formamos BBox
      lon2 = evt.coordinate[0];
      lat2 = evt.coordinate[1];
      primerclick = true;
      // Check that BBox is correctly formed
      // Check lon
      if (lon1>lon2){
        document.getElementById("id_bbox_sw_lon").value = lon2;
        document.getElementById("id_bbox_ne_lon").value = lon1;
      }else{
        document.getElementById("id_bbox_sw_lon").value = lon1;
        document.getElementById("id_bbox_ne_lon").value = lon2;
      }
      // Check lat
      if (lat1>lat2){
        document.getElementById("id_bbox_sw_lat").value = lat2;  
        document.getElementById("id_bbox_ne_lat").value = lat1;  
      }else{
        document.getElementById("id_bbox_sw_lat").value = lat1;  
        document.getElementById("id_bbox_ne_lat").value = lat2;  
      }
    }
  }else{
    primerclick = true;
  }

});
// FIN EVENTOSmapa 

// EVENTOS botones
// Botón DEBUG
botonDebug.onclick = function(){
// Zona DEBUGGING y PRUEBAS
  console.log(typeSelect)

};
// Botón CENTER
botonCenter.onclick = function(){
  // Centramos mapa
  CenterMap(centerLon, centerLat);
};
// Botón SELECT AREA 
// TODO - que sea un toggle en vez de un botón
botonSelectArea.onclick = function(){
  if (draw) srcDraw.clear();
  if (typeSelect == 'Box'){
    typeSelect = 'None';  
  }else{
    typeSelect = 'Box';
  }
  map.removeInteraction(draw);
  addInteraction();
}
// FIN EVENTOS botones
addInteraction();
// ###### FIN EVENTOS ######