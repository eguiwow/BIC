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

import Feature from 'ol/Feature';
import {useGeographic, transform, fromLonLat} from 'ol/proj'
import {getAllTextContent, parse} from 'ol/xml';

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
// https://openlayersbook.github.io/ch06-styling-vector-layers/example-07.html 
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
var json_tracks = document.getElementById("json_tracks")
var json_dtours = document.getElementById("json_dtours")
var json_bidegorris = document.getElementById("json_bidegorris")
var json_air = document.getElementById("json_air")
var json_noise = document.getElementById("json_noise")
// TODO - por qué había que hacer la dataProjection y featureProjection en sourceGJTracks? 
// var gj_tracks = new GeoJSON().readFeatures(JSON.parse(json_tracks.innerText))
var gj_dtours = new GeoJSON().readFeatures(JSON.parse(json_dtours.innerText))
var gj_bidegorris = new GeoJSON().readFeatures(JSON.parse(json_bidegorris.innerText))
var gj_air = new GeoJSON().readFeatures(JSON.parse(json_air.innerText))
var gj_noise = new GeoJSON().readFeatures(JSON.parse(json_noise.innerText))
var botonDebug = document.getElementById("debugButton")
var botonCenter = document.getElementById("centerButton")
// Center & Zoom [From Zaratamap]
var centerLon = JSON.parse(document.getElementById("center").innerText)[0]
var centerLat = JSON.parse(document.getElementById("center").innerText)[1]
var zoom = document.getElementById("zoom").innerText
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

var vTracks = new VectorLayer({
  title: 'tracks',
  visible: false,
  source: sourceGJTracks,
  style: styleFunction,
});
var vDtours = new VectorLayer({
  title: 'dtours',
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

var blur = 30;
var radius = 4;

// HeatMap - https://openlayers.org/en/latest/apidoc/module-ol_layer_Heatmap-Heatmap.html 
// Source = Point[]
var hmTracks = new HeatMapLayer({
  title: 'heatmap_tracks',
  visible: false,
  source: sourceGJTracks,
  blur: blur,
  radius: radius,
  weight: function (feature) {
    // Either extract value from feature or do other thing
    // var name = feature.get('name');
    // var magnitude = parseFloat(name.substr(2));
    return 1;
  },
})
// ###### FIN Layers tipo JSON ######

// ###### Layers tipo KML ######
// TODO - probar bidegorris.kml desde url de Bizkaia 
// --> VectorSource()
// ###### FIN Layers tipo KML ######

var grupoPolucion = new LayerGroup({
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

// Mapa
var map = new Map({
  layers: [osm_tiles, hmTracks, grupoVectores, grupoPolucion], // Capas de información geoespacial
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
  // No sé por qué con el heatmap parece que no funciona
  displayFeatureInfo(evt.pixel);
});
// ###### FIN EVENTOS del mapa ######

// ###### BOTONES ######

botonDebug.onclick = function(){
// Zona DEBUGGING y PRUEBAS
  console.log("111 Deberíamos de ver colores")
};

botonCenter.onclick = function(){
  // Centramos mapa
  CenterMap(centerLon, centerLat);
};

// ###### FIN BOTONES ######