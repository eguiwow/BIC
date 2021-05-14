// **********************************
//           MAPA CONSULTA
// **********************************
import 'ol/ol.css';
import {KML, GPX, GeoJSON} from 'ol/format';
import Map from 'ol/Map';
import VectorSource from 'ol/source/Vector';
import {XYZ, OSM, Stamen} from 'ol/source';
import View from 'ol/View';
import {Circle as CircleStyle, RegularShape, Fill, Stroke, Style} from 'ol/style';
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
// Estilo por defecto
var defaultStyle = new Style({
  image: new CircleStyle({
      fill: new Fill({
          color: 'rgba(165,165,165,0.4)', // GRAY
      }),
      radius: 5,
      stroke: new Stroke({
          color: '#A5A4A4', 
          width: 0.2,
      }),
  }),        
});
// Style de Ruido y Polución
var dangerous = [0,0,0,0.5];    // BLACK > 100dB / 250 PM2.5
var high = [255,0,0,0.5];       // RED: 70-100dB / 120-250 PM2.5
var mid_high = [255,166,0,0.5]  // ORANGE: 65-70 dB / 90-120 PM2.5
var mid = [255,255,0,0.5];      // YELLOW: 60-65 dB / 60-90 PM2.5
var low = [0,255,0,0.5];        // GREEN: 50-60 dB / 30-60 PM2.5
var very_low = [255,255,255,0.9]; // WHITE < 50 dB / 30 PM2.5
// Creamos lista de estilos en función de valor
var styleListNoise = [];
var styleListAir = [];
var values = [dangerous, high, mid_high, mid, low, very_low] // high income
var i, ii;
for (i = 0; i < values.length; i++){
  // Circle for Noise
  styleListNoise[i] = new Style({
    image: new CircleStyle({
        fill: new Fill({
            color: values[i],
        }),
        radius: 7,
        stroke: defaultStyle.stroke,
    }),
  });
  // Rhombus for Air
  styleListAir[i] = new Style({
    image: new RegularShape({
        points: 4,
        fill: new Fill({
            color: values[i],
        }),
        radius: 7,
        stroke: defaultStyle.stroke,
    }),
  });    
}
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
      color: 'rgba(0, 255, 0, 0.5)', // GREEN
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
      color: 'rgba(255, 0, 0, 0.5)', //RED
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
// Devuelve el estilo correspondiente para cada franja de ruido
var styleNoise = function(feature, resolution) {
  // Obtenemos el value de la feature
  var value = feature.get('value');
  // Asignamos estilo a valor
  if (!value) {
      return [defaultStyle];
  }else{
      if (value >= 100){
          return [styleListNoise[0]];
      }else if (value<100 && value >= 70){ 
          return [styleListNoise[1]];
      }else if (value<70 && value >= 65){
          return [styleListNoise[2]];
      }else if (value<65 && value >= 60){
          return [styleListNoise[3]];
      }else if (value<60 && value >= 50){
          return [styleListNoise[4]];
      }else{
          return [styleListNoise[5]];
      }
  }
}

// Devuelve el estilo correspondiente para cada franja de polución
var styleAir = function(feature, resolution) {
  // Obtenemos el value de la feature
  var value = feature.get('value');
  // Asignamos estilo a valor
  if (!value) {
      return [defaultStyle];
  }else{
      if (value >= 250){
          return [styleListAir[0]];
      }else if (value<250 && value >= 120){
          return [styleListAir[1]];
      }else if (value<120 && value >= 90){
          return [styleListAir[2]];
      }else if (value<90 && value >= 60){
          return [styleListAir[3]];
      }else if (value<60 && value >= 30){
          return [styleListAir[4]];
      }else{
          return [styleListAir[5]];
      }
  }
}

// ###### FIN Estilo de pintado de Features ######


// ###### Variables dinámicas ######
var botonVentana = document.getElementById('menu-toggle');
var json_tracks = document.getElementById("json_tracks")
var json_dtours = document.getElementById("json_dtours")
var json_bidegorris = document.getElementById("json_bidegorris")
var json_air = document.getElementById("json_air")
var json_noise = document.getElementById("json_noise")
var gj_tracks = new GeoJSON().readFeatures(JSON.parse(json_tracks.innerText))
var gj_dtours = new GeoJSON().readFeatures(JSON.parse(json_dtours.innerText))
var gj_air = new GeoJSON().readFeatures(JSON.parse(json_air.innerText))
var gj_noise = new GeoJSON().readFeatures(JSON.parse(json_noise.innerText))
// TODO meter temperatura
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
var sourceGJAir = new VectorSource({
  wrapX:false,
  features: gj_air
});
var sourceGJNoise = new VectorSource({
  wrapX:false,
  features: gj_noise
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
var vAir = new VectorLayer({
  title: 'cont. atmosférica',
  visible: false,
  source: sourceGJAir,
  style: styleAir,
});
var vNoise = new VectorLayer({
  title: 'cont. acústica',
  visible: true,
  source: sourceGJNoise,
  style: styleNoise,
});

// Capa para Draw
var srcDraw = new VectorSource({wrapX: false});
var vDraw = new VectorLayer({source: srcDraw,});

// Número de tracks
var tracksLength = vTracks.getSource().getFeatures().length;

var grupoSensorica = new LayerGroup({
  title: 'Polución',
  layers: [vAir, vNoise],  
})

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
  layers: [osm_tiles, grupoVectores, grupoSensorica, vDraw], // Capas de información geoespacial
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
// Display Feature Info - https://openlayers.org/en/latest/examples/gpx.html 
// Esta función saca información de las features al pinchar (ahora mismo el 'name')
// TODO - 
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
  console.log(loc); // saca la ruta de la URL
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
        document.getElementById("id_SW_lon").value = lon2;
        document.getElementById("id_NE_lon").value = lon1;
      }else{
        document.getElementById("id_SW_lon").value = lon1;
        document.getElementById("id_NE_lon").value = lon2;
      }
      // Check lat
      if (lat1>lat2){
        document.getElementById("id_SW_lat").value = lat2;  
        document.getElementById("id_NE_lat").value = lat1;  
      }else{
        document.getElementById("id_SW_lat").value = lat1;  
        document.getElementById("id_NE_lat").value = lat2;  
      }
    }
  }else{ // Si no estamos en modo 'Box' sacamos info feature
    displayFeatureInfo(evt.pixel);
    primerclick = true;
  }

});

botonVentana.onclick = function() {
  setTimeout( function() { map.updateSize();}, 200);
};

// FIN EVENTOSmapa 

// EVENTOS botones
// Botón DEBUG
botonDebug.onclick = function(){
// Zona DEBUGGING y PRUEBAS
  console.log("Jejeejjeje");  

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