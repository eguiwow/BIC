// **********************************
//            MAPA BASE
// **********************************
import 'ol/ol.css';
import {KML, GPX, GeoJSON} from 'ol/format';
import Map from 'ol/Map';
import VectorSource from 'ol/source/Vector';
import {XYZ, OSM, Stamen} from 'ol/source';
import View from 'ol/View';
import {Circle as CircleStyle, Fill, Stroke, Style} from 'ol/style';
import {Tile as TileLayer, Vector as VectorLayer, Group as LayerGroup} from 'ol/layer';
import LayerSwitcher from 'ol-layerswitcher';
import Overlay from 'ol/Overlay';
import {toStringHDMS} from 'ol/coordinate';

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

// ###### FIN Estilo de pintado de Features ######


// ###### Variables dinámicas ######
var botonVentana = document.getElementById('menu-toggle');
var json_tracks = document.getElementById("json_tracks")
var json_dtours = document.getElementById("json_dtours")
var json_bidegorris = document.getElementById("json_bidegorris")
var gj_tracks = new GeoJSON().readFeatures(JSON.parse(json_tracks.innerText))
var gj_dtours = new GeoJSON().readFeatures(JSON.parse(json_dtours.innerText))
var gj_bidegorris = new GeoJSON().readFeatures(JSON.parse(json_bidegorris.innerText))
var botonDebug = document.getElementById("debugButton")
var botonCenter = document.getElementById("centerButton")
var botonDownload = document.getElementById('export-png')
// Center & Zoom [From Zaratamap]
var centerLon = JSON.parse(document.getElementById("center").innerText)[0]
var centerLat = JSON.parse(document.getElementById("center").innerText)[1]
var zoom = document.getElementById("zoom").innerText
// Vars features
var ratio;
var ratioChanged = false;
var length = 0;
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
  source: sourceGJTracks,
  style: styleFunction,
});
var vDtours = new VectorLayer({
  title: 'dtours',
  source: sourceGJDtours,
  style: styleFunction2,
});
var vBidegorris = new VectorLayer({
  title: 'bidegorris',
  source: sourceGJBidegorris,
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
var grupoVectores = new LayerGroup({
  title: 'Capas',
  layers: [vTracks, vDtours, vBidegorris],
})
// LayerSwitcher (para cambiar entre capas) - https://github.com/walkermatt/ol-layerswitcher 
var layerSwitcher = new LayerSwitcher();

// Mapa
var map = new Map({
  layers: [osm_tiles, grupoVectores], // Capas de información geoespacial
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

// VARIABLES OVERLAY
// LonLat de Bilbao
var pos = [centerLon, centerLat];
// Popup que se va a generar en el html
var popup = new Overlay({
  element: document.getElementById('popup'),
});
map.addOverlay(popup);

// Bilbao marker
var marker = new Overlay({
  position: pos,
  positioning: 'center-center',
  element: document.getElementById('marker'),
  stopEvent: false,
});
map.addOverlay(marker);

// Bilbao label
var bilbao = new Overlay({
  position: pos,
  element: document.getElementById('bilbao'),
});
map.addOverlay(bilbao);

map.on('click', function (evt) {

});

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
  // Guardamos 'length' y 'ratio' cuando haya
  if (features.length > 0) {
    var info = [];
    for (i = 0, ii = features.length; i < ii; ++i) {
      length = parseFloat(features[i].get('length')); // Sacamos length track    
      info.push(length.toFixed(2));
      if (features[i].get('ratio')){
        length = parseFloat(features[i].get('length')); // Sacamos length de Dtour 
        ratio = parseFloat(features[i].get('ratio')); // Sacamos ratio en Dtours
        info.push(ratio.toFixed(2));
        ratioChanged = true;
      }
    }
    map.getTarget().style.cursor = 'pointer';
    // Parte de PopUp
    var element = popup.getElement();
    var hdms = toStringHDMS(coords);

    popup.setPosition(coords);
    if (ratioChanged){
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
    $(element).popover('show');
  } else { // No hay info en las features
    map.getTarget().style.cursor = '';
  }
};

// Centrar Mapa - https://gis.stackexchange.com/questions/112892/change-openlayers-3-view-center
function CenterMap(long, lati) {
  // map.getView().setCenter(fromLonLat([long, lati]));
  map.getView().setCenter([long, lati]);
  map.getView().setZoom(13);
}

botonVentana.onclick = function() {
  setTimeout( function() { map.updateSize();}, 200);
  console.log("AUI");
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

// Click
map.on('click', function (evt) {  
  displayFeatureInfo(evt.pixel, evt.coordinate);
});
// ###### FIN EVENTOS del mapa ######

// ###### BOTONES ######

// Botón DEBUGGING y PRUEBAS
botonDebug.onclick = function(){
  var i, ii;
  console.log("JUJU5");
  console.log(ratio);
  console.log(length);   
};
// Botón centrar mapa
botonCenter.onclick = function(){
  CenterMap(centerLon, centerLat);
};
  
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