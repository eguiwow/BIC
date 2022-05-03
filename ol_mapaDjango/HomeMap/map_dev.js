// **********************************
//            MAPA MOVILIDAD
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
import Overlay from 'ol/Overlay';
import Draw, {createBox} from 'ol/interaction/Draw';
import {toStringHDMS} from 'ol/coordinate';

import Feature from 'ol/Feature';
import {useGeographic, transform, fromLonLat} from 'ol/proj'
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

// Tiles de OpenStreetMaps
var osm_tiles = new TileLayer({
  type: 'base', // Indicamos que es mapa base para el LayerSwitcher 
  source: new OSM(),
});

// ###### Estilo de pintado de Features ######
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
// https://openlayersbook.github.io/ch06-styling-vector-layers/example-07.html 
// Style de Retardo
var dangerous = [0,0,0,0.5];      // BLACK 
var high = [255,0,0,0.5];         // RED: 
var mid_high = [255,166,0,0.5]    // ORANGE: 
var mid = [255,255,0,0.5];        // YELLOW:
var low = [0,255,0,0.5];          // GREEN: 
var very_low = [255,255,255,0.9]; // WHITE 

// Creamos lista de estilos en función de valor
var styleListRetardo = [];
var styleListVel = [];
var values = [dangerous, high, mid_high, mid, low, very_low] 
var i, ii;
for (i = 0; i < values.length; i++){
  styleListRetardo[i] = new Style({
    image: new CircleStyle({
        fill: new Fill({
            color: values[i],
        }),
        radius: 7,
        stroke: defaultStyle.stroke,
    }),
  });
}
// Style de Velocidad
var fire = [0,0,0,0.5];       // BLACK > 40
var hot = [255,0,0,0.5];      // RED 35-40
var mid_hot = [255,166,0,0.5] // ORANGE 25-35
var mild = [255,255,0,0.5];   // YELLOW 15-25
var mid_cold = [90,180,255,0.5]; // LIGHT BLUE 5-15
var cold = [90,90,190,0.9]; // DARK BLUE  0-5
var ice = [255,255,255,0.9];  // WHITE < 0ºC 

var valuesVel = [fire, hot, mid_hot, mild, mid_cold, cold, ice] 

for (i=0; i< valuesVel.length; i++){
styleListVel[i] = new Style({
  image: new CircleStyle({
      fill: new Fill({
          color: valuesVel[i],
      }),
      radius: 7,
      stroke: defaultStyle.stroke,
  }),
});
}

// Style General
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
      color: 'rgba(0, 170, 60, 0.7)', // GREEN
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
      color: 'rgba(0, 0, 255, 0.1)', // BLUE
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
      color: 'rgba(255, 0, 0, 0.7)', //RED
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
var styleRetardo = function(feature, resolution) {
  // Obtenemos el value de la feature
  var value = feature.get('value');
  // Asignamos estilo a valor
  if (!value) {
      return [defaultStyle];
  }else{
    if (value >= 40){
      return [styleListRetardo[5]];
    }else if (value<40 && value >= 30){ 
        return [styleListRetardo[4]];
    }else if (value<30 && value >= 20){
        return [styleListRetardo[3]];
    }else if (value<20 && value >= 10){
        return [styleListRetardo[2]];
    }else if (value<10 && value >= 5){
        return [styleListRetardo[1]];
    }else{
        return [styleListRetardo[0]];
    }
  }
}
// Devuelve el estilo correspondiente para cada franja de ruido
// Uso al final el styleRetardo al revés para velocidad
var styleVel = function(feature, resolution) {
  // Obtenemos el value de la feature
  var value = feature.get('value');
  // Asignamos estilo a valor
  if (!value) {
      return [defaultStyle];
  }else{
    if (value >= 40){
      return [styleListRetardo[0]];
    }else if (value<40 && value >= 30){ 
        return [styleListRetardo[1]];
    }else if (value<30 && value >= 20){
        return [styleListRetardo[2]];
    }else if (value<20 && value >= 10){
        return [styleListRetardo[3]];
    }else if (value<10 && value >= 5){
        return [styleListRetardo[4]];
    }else{
        return [styleListRetardo[5]];
    }
  }
}

// ###### FIN Estilo de pintado de Features ######


// ###### Variables dinámicas ######
var json_tracks = document.getElementById("json_tracks")
var json_points = document.getElementById("json_points")
var json_dtours = document.getElementById("json_dtours")
var json_dpoints = document.getElementById("json_dpoints")
var json_bidegorris = document.getElementById("json_bidegorris")
var json_vel = document.getElementById("json_vel")
var gj_tracks = new GeoJSON().readFeatures(JSON.parse(json_tracks.innerText))
var gj_dtours = new GeoJSON().readFeatures(JSON.parse(json_dtours.innerText))
var gj_bidegorris = new GeoJSON().readFeatures(JSON.parse(json_bidegorris.innerText))
var gj_vel = new GeoJSON().readFeatures(JSON.parse(json_vel.innerText))
// Botones
var botonVentana = document.getElementById('menu-toggle')
var botonDebug = document.getElementById("debugButton")
var botonCenter = document.getElementById("centerButton")
var botonSelectArea = document.getElementById("selectAreaButton")
var botonDownload = document.getElementById('export-png')
var switchHM = document.getElementById("switchHM")
var switchHM2 = document.getElementById("switchHM2")
// Form
var since_default = document.getElementById("since_default")
var until_default = document.getElementById("until_default")
var ne_lon = document.getElementById("id_NE_lon").value;
var ne_lat = document.getElementById("id_NE_lat").value;
var sw_lon = document.getElementById("id_SW_lon").value;
var sw_lat = document.getElementById("id_SW_lat").value;
var consulta_vacia = document.getElementById("consulta_vacia");
var lon1, lon2, lat1, lat2;
// Center & Zoom [From Zaratamap]
var centerLon = JSON.parse(document.getElementById("center").innerText)[0]
var centerLat = JSON.parse(document.getElementById("center").innerText)[1]
var zoom = parseInt(document.getElementById("zoom").innerText)
// Vars features
var ratio;
var length = 0;
var units;
var value;
var timestamp;
var ratioChanged = false;
var isTrack = false;
var isSensor = false;
// Vars heatmap
var blur = 32;
var radius = 2;
// ###### FIN Variables dinámicas ######

// ###### Layers tipo JSON ######
var sourceGJTracks = new VectorSource({
  wrapX: false,
  features: gj_tracks
});
var sourceGJTrackpoints = new VectorSource({
  wrapX: false,
  features: new GeoJSON().readFeatures(json_points.innerText, {
    dataProjection: "EPSG:4326",
    featureProjection: "EPSG:4326"
  })
});
var sourceGJDtourpoints = new VectorSource({
  wrapX: false,
  features: new GeoJSON().readFeatures(json_dpoints.innerText, {
    dataProjection: "EPSG:4326",
    featureProjection: "EPSG:4326"
  })
});
var sourceGJDtours = new VectorSource({
  wrapX: false,
  features: gj_dtours
});
var sourceGJBidegorris = new VectorSource({
  wrapX:false,
  features: gj_bidegorris
});
var sourceGJVel = new VectorSource({
  wrapX:false,
  features: gj_vel
});

var vTracks = new VectorLayer({
  title: 'rutas',
  source: sourceGJTracks,
  style: styleFunction,
});
var vDtours = new VectorLayer({
  title: 'desvíos',
  source: sourceGJDtours,
  style: styleFunction2,
});
var vBidegorris = new VectorLayer({
  title: 'bidegorris',
  source: sourceGJBidegorris,
  style: styleFunction,
});
var vRetardo = new VectorLayer({
  title: 'retardo',
  source: sourceGJVel,
  style: styleRetardo,
});
var vVelocidad = new VectorLayer({
  title: 'velocidad',
  source: sourceGJVel,
  style: styleVel,
});

// var hmTracks = new HeatMapLayer({
//   title: 'heatmap_rutas',
//   visible: false,
//   source: sourceGJTrackpoints,
//   blur: blur,
//   radius: radius,
//   weight: function (feature) {
//     // Either extract value from feature or do other thing
//     // var name = feature.get('vel');
//     // var magnitude = parseFloat(name.substr(2));
//     return 1;
//   },
// })
var hmTracks = new HeatMapLayer({
  title: 'heatmap_rutas',
  visible: false,
  source: sourceGJVel,
  blur: blur,
  radius: radius,
  weight: function (feature) {
    // Either extract value from feature or do other thing
    var value = feature.get('value');
    var magnitude = parseFloat(value);
    console.log(magnitude)
    return magnitude;
  },
})
var hmDtours = new HeatMapLayer({
  title: 'heatmap_desvíos',
  visible: false,
  source: sourceGJDtourpoints,
  blur: (blur-25),
  radius: radius,
  weight: function (feature) {
    // Either extract value from feature or do other thing
    // var name = feature.get('name');
    // var magnitude = parseFloat(name.substr(2));
    return 1;
  },
})
// ###### FIN Layers tipo JSON ######

// Capa para Draw
var srcDraw = new VectorSource({wrapX: false});
var vDraw = new VectorLayer({source: srcDraw,});

// LayerSwitcher (para cambiar entre capas) - https://github.com/walkermatt/ol-layerswitcher 
var layerSwitcher = new LayerSwitcher();
var typeSelect = 'None';

// Mapa
var map = new Map({
  layers: [osm_tiles, vDtours, vBidegorris, vRetardo, vVelocidad, vTracks, vDraw], // Capas de información geoespacial
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

// Popup que se va a generar en el html
var popup = new Overlay({
  element: document.getElementById('popup'),
});
map.addOverlay(popup);

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
// Display Feature Info --> example OpenLayers 
var displayFeatureInfo = function (pixel, coords) {
  $(element).popover('dispose');
  // Parte recogida features
  var features = [];
  var i, ii;
  // Recogemos todas las features del pixel seleccionado
  map.forEachFeatureAtPixel(pixel, function (feature) {
    features.push(feature);
  });
  if (features.length > 0) { // Hay Features, recogemos los datos
    var info = [];
    for (i = 0, ii = features.length; i < ii; ++i) {
      if (features[i].get('length')){
        length = parseFloat(features[i].get('length')); // Sacamos length track / bidegorri / dtour  
        info.push(length.toFixed(2));
        if (features[i].get('ratio')){ // Es Dtour
          length = parseFloat(features[i].get('length')); // Sacamos length de Dtour 
          ratio = parseFloat(features[i].get('ratio')); // Sacamos ratio en Dtours
          info.push(ratio.toFixed(2));
          ratioChanged = true;
        }
        if (features[i].get('time')){ // Es Track
          timestamp = features[i].get('time'); // Sacamos time en track
          info.push(timestamp);
          isTrack = true;
        }
      }else if(features[i].get('value')){ // Es Trackpoint
        isSensor = true;
        value = parseFloat(features[i].get('value')); // Sacamos value
        info.push(value.toFixed(2));
        units = features[i].get('units'); // Sacamos units 
        info.push(units);
        timestamp = features[i].get('time'); // Sacamos timestamp
        info.push(timestamp);
      }
    }
    map.getTarget().style.cursor = 'pointer';
    // Parte de PopUp
    var element = popup.getElement();
    var hdms = toStringHDMS(coords);

    popup.setPosition(coords);

    if(isSensor){ // Measurement
      isSensor = false;
      $(element).popover("dispose").popover({
        container: element,
        placement: 'top',
        animation: false,
        html: true,
        content: 
        '<p>Location: ' + coords[0].toFixed(4) + 'º lon, '+ coords[1].toFixed(4) + 'º lat</p>'+
        '<p>Velocity: ' + value.toFixed(2) + 'km/h' + '</p>'+
        '<p>Date & Time: ' + timestamp.substring(0,19) + '</p>',
      });      
    }else{ 
      if (ratioChanged){ // Dtour
        ratioChanged = false;
        $(element).popover("dispose").popover({
          container: element,
          placement: 'top',
          animation: false,
          html: true,
          content: 
          '<p>Dtour\'s length: ' + length.toFixed(2) + 'm</p>'+
          '<p>Ratio dtour/track: '+ ratio.toFixed(2) + '%</p>' +
          '<p>Location: ' + coords[0].toFixed(4) + 'º lon, '+ coords[1].toFixed(4) + 'º lat</p>',
        });
      }else{
        if (isTrack){ // Track
          isTrack = false;
          $(element).popover("dispose").popover({
            container: element,
            placement: 'top',
            animation: false,
            html: true,
            content: 
            '<p>Track\'s length: ' + length.toFixed(2) + 'm</p>'+
            '<p>Location: ' + coords[0].toFixed(4) + 'º lon, '+ coords[1].toFixed(4) + 'º lat</p>'+
            '<p>Date & Time: ' + timestamp.substring(0,19) + '</p>',
          });
        }else{ // Bidegorri
          $(element).popover("dispose").popover({
            container: element,
            placement: 'top',
            animation: false,
            html: true,
            content: 
            '<p>Track\'s length: ' + length.toFixed(2) + 'm</p>'+
            '<p>Location: ' + coords[0].toFixed(4) + 'º lon, '+ coords[1].toFixed(4) + 'º lat</p>',
          });
        }
      }
    }
    $(element).popover('show');
  } else { // No hay info en las features
    map.getTarget().style.cursor = '';
  }
};

// Centrar Mapa - https://gis.stackexchange.com/questions/112892/change-openlayers-3-view-center
function CenterMap(long, lati) {
  // map.getView().setCenter(fromLonLat([long, lati]));
  map.getView().setCenter([long, lati]);
  map.getView().setZoom(zoom);
}

function getDate() {
  var today = new Date();
  var lastYear = new Date();
  var dd = today.getDate();
  var mm = today.getMonth()+1; //January is 0!
  var yyyy = today.getFullYear();
  if(dd<10) {
      dd = '0'+dd
  } 

  if(mm<10) {
      mm = '0'+mm
  } 

  today = yyyy + '/' + mm + '/' + dd;
  lastYear = yyyy-1 + '/' + mm + '/' + dd;
  console.log(today);
  document.getElementById("id_since_datetime").value = lastYear;
  document.getElementById("id_until_datetime").value = today;

}

// Cambio entre Rutas normal y HM
function normalToHeatmapTracks(){
  if (switchHM.checked){
    map.getLayers().getArray()
      .filter(layer => layer.get('title') === 'rutas')
      .forEach(layer => map.removeLayer(layer));
    map.addLayer(hmTracks);
  }else{
    map.getLayers().getArray()
      .filter(layer => layer.get('title') === 'heatmap_rutas')
      .forEach(layer => map.removeLayer(layer));
      map.addLayer(vTracks);
  }
}

// Cambio entre Desvío normal y HM
function normalToHeatmapDtours(){
  if (switchHM2.checked){
    map.getLayers().getArray()
      .filter(layer => layer.get('title') === 'desvíos')
      .forEach(layer => map.removeLayer(layer));
    map.addLayer(hmDtours);
  }else{
    map.getLayers().getArray()
      .filter(layer => layer.get('title') === 'heatmap_desvíos')
      .forEach(layer => map.removeLayer(layer));
      map.addLayer(vDtours);
  }
}

// OnLoad (window)
window.onload = function() {
  // Calcular fecha
  getDate();
  // Si la consulta es vacía --> sacamos alerta 
  if (consulta_vacia.innerText == 1){
    alert("No existe actividad en este rango, prueba a cambiar el rango temporal o espacial")
  }
};
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

var primerclick = true;
// Click
map.on('click', function (evt) {  
  // evt.coordinate guarda las coordenadas del evento de click
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
    displayFeatureInfo(evt.pixel, evt.coordinate);
    primerclick = true;
  }
});

// ###### FIN EVENTOS del mapa ######

// ###### BOTONES ######
botonVentana.onclick = function() {
  setTimeout( function() { map.updateSize();}, 200);
};

// Botón DEBUGGING y PRUEBAS
botonDebug.onclick = function(){
  var i, ii;
  console.log("ª");
  console.log(centerLon)   
  console.log(centerLat)
  console.log(zoom)
};
// Botón centrar mapa
botonCenter.onclick = function(){
  CenterMap(centerLon, centerLat);
};
switchHM.onchange = function(){
  normalToHeatmapTracks();
}
switchHM2.onchange = function(){
  normalToHeatmapDtours();
}  

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

// Botón exportar como PNG
// https://openlayers.org/en/latest/examples/export-map.html
botonDownload.onclick = function(){
  map.once('rendercomplete', function () {
    var mapCanvas = document.createElement('canvas');
    var size = map.getSize();
    mapCanvas.width = size[0];
    mapCanvas.height = size[1];
    var mapContext = mapCanvas.getContext('2d');
    Array.prototype.forEach.call(
      document.querySelectorAll('.ol-layer canvas'),
      function (canvas) {
        if (canvas.width > 0) {
          var opacity = canvas.parentNode.style.opacity;
          mapContext.globalAlpha = opacity === '' ? 1 : Number(opacity);
          var transform = canvas.style.transform;
          // Get the transform parameters from the style's transform matrix
          var matrix = transform
            .match(/^matrix\(([^\(]*)\)$/)[1]
            .split(',')
            .map(Number);
          // Apply the transform to the export map context
          CanvasRenderingContext2D.prototype.setTransform.apply(
            mapContext,
            matrix
          );
          mapContext.drawImage(canvas, 0, 0);
        }
      }
    );
    if (navigator.msSaveBlob) {
      // link download attribuute does not work on MS browsers
      navigator.msSaveBlob(mapCanvas.msToBlob(), 'map.png');
    } else {
      var link = document.getElementById('image-download');
      link.href = mapCanvas.toDataURL();
      link.click();
    }
  });
  map.renderSync();
};

addInteraction();
// ###### FIN BOTONES ######