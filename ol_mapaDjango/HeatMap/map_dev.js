// **********************************
//          MAPA DE CALOR
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
import Overlay from 'ol/Overlay';
import {toStringHDMS} from 'ol/coordinate';

import Feature from 'ol/Feature';
import {useGeographic, transform, fromLonLat} from 'ol/proj'
import {getAllTextContent, parse} from 'ol/xml';

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
// https://openlayersbook.github.io/ch06-styling-vector-layers/example-07.html 
// Style de Ruido y Polución
var dangerous = [0,0,0,0.5];      // BLACK > 100dB / 75 PM2.5
var high = [255,0,0,0.5];         // RED: 80-100dB / 50-75 PM2.5
var mid_high = [255,166,0,0.5]    // ORANGE: 70-80 dB / 25-50 PM2.5
var mid = [255,255,0,0.5];        // YELLOW: 60-70 dB / 20-25 PM2.5
var low = [0,255,0,0.5];          // GREEN: 40-60 dB / 10-20 PM2.5
var very_low = [255,255,255,0.9]; // WHITE < 40 dB / 10 PM2.5

// Creamos lista de estilos en función de valor
var styleListNoise = [];
var styleListAir = [];
var styleListTemp = [];
var values = [dangerous, high, mid_high, mid, low, very_low] 
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
// Style de temperatura
var fire = [0,0,0,0.5];       // BLACK > 40
var hot = [255,0,0,0.5];      // RED 35-40
var mid_hot = [255,166,0,0.5] // ORANGE 25-35
var mild = [255,255,0,0.5];   // YELLOW 15-25
var mid_cold = [90,180,255,0.5]; // LIGHT BLUE 5-15
var cold = [90,90,190,0.9]; // DARK BLUE  0-5
var ice = [255,255,255,0.9];  // WHITE < 0ºC 

var valuesTemp = [fire, hot, mid_hot, mild, mid_cold, cold, ice] 

for (i=0; i< valuesTemp.length; i++){
  styleListTemp[i] = new Style({
    image: new CircleStyle({
        fill: new Fill({
            color: valuesTemp[i],
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
        color: 'rgba(255,255,0,0.5)',
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
        color: 'rgba(255,255,0,0.5)',
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
    }else if (value<100 && value >= 80){ 
        return [styleListNoise[1]];
    }else if (value<80 && value >= 70){
        return [styleListNoise[2]];
    }else if (value<70 && value >= 60){
        return [styleListNoise[3]];
    }else if (value<60 && value >= 40){
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
    if (value >= 75){
        return [styleListAir[0]];
    }else if (value<75 && value >= 50){
        return [styleListAir[1]];
    }else if (value<50 && value >= 25){
        return [styleListAir[2]];
    }else if (value<25 && value >= 20){
        return [styleListAir[3]];
    }else if (value<20 && value >= 10){
        return [styleListAir[4]];
    }else{
        return [styleListAir[5]];
    }
  }
}
// Devuelve el estilo correspondiente para cada franja de temperatura
var styleTemp = function(feature, resolution) {
  // Obtenemos el value de la feature
  var value = feature.get('value');
  // Asignamos estilo a valor
  if (!value) {
      return [defaultStyle];
  }else{
      if (value >= 40){
          return [styleListTemp[0]];
      }else if (value<40 && value >= 35){
          return [styleListTemp[1]];
      }else if (value<35 && value >= 25){
          return [styleListTemp[2]];
      }else if (value<25 && value >= 15){
          return [styleListTemp[3]];
      }else if (value<15 && value >= 5){
          return [styleListTemp[4]];
      }else if (value<5 && value >= 0){
          return [styleListTemp[5]];
      }else{
        return [styleListTemp[6]];
      }
  }
}
// ###### FIN Estilo de pintado de Features ######


// ###### Variables dinámicas ######
var json_tracks = document.getElementById("json_tracks")
var json_dtours = document.getElementById("json_dtours")
var json_bidegorris = document.getElementById("json_bidegorris")
var json_air = document.getElementById("json_air")
var json_noise = document.getElementById("json_noise")
var json_temp = document.getElementById("json_temp")
// TODO - por qué había que hacer la dataProjection y featureProjection en sourceGJTracks? 
// var gj_tracks = new GeoJSON().readFeatures(JSON.parse(json_tracks.innerText))
var gj_dtours = new GeoJSON().readFeatures(JSON.parse(json_dtours.innerText))
var gj_bidegorris = new GeoJSON().readFeatures(JSON.parse(json_bidegorris.innerText))
var gj_air = new GeoJSON().readFeatures(JSON.parse(json_air.innerText))
var gj_noise = new GeoJSON().readFeatures(JSON.parse(json_noise.innerText))
var gj_temp = new GeoJSON().readFeatures(JSON.parse(json_temp.innerText))
// Buttons
var botonDebug = document.getElementById("debugButton")
var botonCenter = document.getElementById("centerButton")
var botonVentana = document.getElementById("menu-toggle")
var botonDownload = document.getElementById('export-png')
var switchHM = document.getElementById("switchHM")
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
var isSensor = false;
var isTrack = false;
// Vars heatmap
var blur = 30;
var radius = 4;
// ###### FIN Variables dinámicas ######

// ###### Layers tipo JSON ######
var sourceGJTracks = new VectorSource({
  wrapX: false,
  features: new GeoJSON().readFeatures(json_tracks.innerText, {
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
var sourceGJAir = new VectorSource({
  wrapX:false,
  features: gj_air
});
var sourceGJNoise = new VectorSource({
  wrapX:false,
  features: gj_noise
});
var sourceGJTemp = new VectorSource({
  wrapX:false,
  features: gj_temp
});

var vTracks = new VectorLayer({
  title: 'rutas',
  visible: false,
  source: sourceGJTracks,
  style: styleFunction,
});
var vDtours = new VectorLayer({
  title: 'desvíos',
  visible: false,
  source: sourceGJDtours,
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
var vTemp = new VectorLayer({
  title: 'temperatura',
  visible: true,
  source: sourceGJTemp,
  style: styleTemp,
});

// HeatMap - https://openlayers.org/en/latest/apidoc/module-ol_layer_Heatmap-Heatmap.html 
// Source = Point[]

var hmTemp = new HeatMapLayer({
  title: 'heatmap_temperatura',
  visible: false,
  source: sourceGJTemp,
  blur: blur,
  radius: radius,
  weight: function (feature) {
    // Either extract value from feature or do other thing
    var value = parseFloat(feature.get('value'));
    // return value;
    return value;
  },
})
// ###### FIN Layers tipo JSON ######

var grupoPolucion = new LayerGroup({
  title: 'Contaminación',
  layers: [vAir, vNoise],  
})

// Grupo de Layers para LayerSwitcher
var grupoVectores = new LayerGroup({
  title: 'Movilidad',
  layers: [vTracks, vDtours, vBidegorris],
})
// LayerSwitcher (para cambiar entre capas) - https://github.com/walkermatt/ol-layerswitcher 
var layerSwitcher = new LayerSwitcher();

// Mapa
var map = new Map({
  layers: [osm_tiles, grupoVectores, grupoPolucion, vTemp], // Capas de información geoespacial
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


// ###### Funciones ######
// Display Feature Info --> example OpenLayers 
var displayFeatureInfo = function (pixel, coords) {
  $(element).popover('dispose');
  var features = [];
  var i, ii;
  // Recogemos todas las features del pixel seleccionado
  map.forEachFeatureAtPixel(pixel, function (feature) {
    features.push(feature);
  });
  // Guardamos properties dependiendo del tipo de geojson
  if (features.length > 0) {
    var info = [];
    for (i = 0, ii = features.length; i < ii; ++i) {
      if (features[i].get('length')){
        length = parseFloat(features[i].get('length')); // Sacamos length track    
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
      }else if(features[i].get('value')){ // Es Measurement
        isSensor = true;
        value = parseFloat(features[i].get('value')); // Sacamos value
        info.push(length.toFixed(2));
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
        '<p>Value: ' + value.toFixed(2) + units + '</p>'+
        '<p>Location: ' + coords[0].toFixed(4) + 'º lon, '+ coords[1].toFixed(4) + 'º lat</p>'+
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

  } else {
    map.getTarget().style.cursor = '';
  }  
};
// Centrar Mapa 
// src: https://gis.stackexchange.com/questions/112892/change-openlayers-3-view-center
function CenterMap(long, lati) {
  map.getView().setCenter([long, lati]);
  map.getView().setZoom(zoom);
}

// Cambio entre Temperatura Heatmap y temperatura puntos
function normalToHeatmapTemp(){
  if (switchHM.checked){
    map.getLayers().getArray()
      .filter(layer => layer.get('title') === 'temperatura')
      .forEach(layer => map.removeLayer(layer));
    map.addLayer(hmTemp);
  }else{
    map.getLayers().getArray()
      .filter(layer => layer.get('title') === 'heatmap_temperatura')
      .forEach(layer => map.removeLayer(layer));
      map.addLayer(vTemp);
  }
}
// ###### FIN Funciones ######

// ###### EVENTOS del mapa ######
// Drag
map.on('pointermove', function (evt) {
  if (evt.dragging) {
    return;
  }
});

// Click
map.on('click', function (evt) {
  // No sé por qué con el heatmap parece que no funciona
  displayFeatureInfo(evt.pixel, evt.coordinate);
});

botonVentana.onclick = function() {
  setTimeout( function() { map.updateSize();}, 200);
};

// ###### FIN EVENTOS del mapa ######

// ###### BOTONES ######

botonDebug.onclick = function(){
// Zona DEBUGGING y PRUEBAS
  console.log("Hirule")
};

botonCenter.onclick = function(){
  // Centramos mapa
  CenterMap(centerLon, centerLat);
};

switchHM.onchange = function(){
  normalToHeatmapTemp();
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

// ###### FIN BOTONES ######