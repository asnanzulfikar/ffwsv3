<!doctype html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">

    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.6.0/dist/leaflet.css"
   integrity="sha512-xwE/Az9zrjBIphAcBb3F6JVqxf46+CDLwfLMHloNu6KEQCAWi6HcDUbeOfBIptF7tcCzusKFjFw2yuvEpDL9wQ=="
   crossorigin=""/>

   <!-- Make sure you put this AFTER Leaflet's CSS -->
   <script src="https://unpkg.com/leaflet@1.6.0/dist/leaflet.js"
     integrity="sha512-gZwIG9x3wUXg2hdXF6+rVkLF/0Vi9U8D2Ntg4Ga5I5BZpVkVxlJWbSQtXPSiUTtC0TjtGOmxa1AJPuV0CPthew=="
     crossorigin=""></script>

     <style>
     	html, body, #container /*, and all other map parent selectors*/ {
		  height: 100%;
		  overflow: hidden;
		  width: 100%;
		}
       #mapid { height: 100%;width: auto }
     </style>

    <title>Leaflet JS</title>
  </head>
  <body>

  	<div id="container">
  		<div id="mapid"></div>
  	</div>
    

    <script src="../static/js/gis/batas_das.js" type="text/javascript"></script>
    <script src="../static/js/gis/tanggul_bojonegoro.js" type="text/javascript"></script>
    <script src="../static/js/gis/bendungan.js" type="text/javascript"></script>
    <script src="../static/js/gis/bendungan_on_going.js" type="text/javascript"></script>
    <script src="../static/js/gis/embung.js" type="text/javascript"></script>
    <script src="../static/js/gis/tanggul_pacitan.js" type="text/javascript"></script>

    <script>

      var mbAttr = 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
          '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
          'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        mbUrl = 'https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw';

      var grayscale   = L.tileLayer(mbUrl, {id: 'mapbox/light-v9', tileSize: 512, zoomOffset: -1, attribution: mbAttr}),
        streets  = L.tileLayer(mbUrl, {id: 'mapbox/streets-v11', tileSize: 512, zoomOffset: -1, attribution: mbAttr});

      var map = L.map('mapid', {
        center: [-7.49592,111.568909],
        zoom: 9,
        layers: [streets]
      });

        var tanggul_icon = L.icon({
          iconUrl: '../static/image/tanggul.png',
          iconSize: [20, 20],
          iconAnchor: [16, 37],
          popupAnchor: [0, -28]
        });

        var embung_icon = L.icon({
          iconUrl: '../static/image/embung.png',
          iconSize: [20, 20],
          iconAnchor: [16, 37],
          popupAnchor: [0, -28]
        });

      var batas_das = L.geoJSON(batas_das, {
        filter: function (feature, layer) {
          if (feature.properties) {
            // If the property "underConstruction" exists and is true, return false (don't render features under construction)
            return feature.properties.underConstruction !== undefined ? !feature.properties.underConstruction : true;
          }
          return false;
        },
        onEachFeature: function(feature,layer){
          var popupContent = "";
          if (feature.properties) {
            popupContent += feature.properties.NAMA_DAS;
          }
          layer.bindPopup(popupContent);
        },
        fillOpacity: 0.1
      }).addTo(map);

      var tanggul_bojonegoro = L.geoJSON(tanggul_bojonegoro, {
        pointToLayer: function (feature, latlng) {
          return L.marker(latlng, {icon: tanggul_icon});
        },
        filter: function (feature, layer) {
          if (feature.properties) {
            // If the property "underConstruction" exists and is true, return false (don't render features under construction)
            return feature.properties.underConstruction !== undefined ? !feature.properties.underConstruction : true;
          }
          return false;
        },
        onEachFeature: function(feature,layer){
          var popupContent = "";
          if (feature.properties) {
            popupContent += "<table border='2'>";
            popupContent += "<tbody>";
            popupContent += "<td colspan='2' class='text-center'><b>Tanggul Bojonegoro</b></td>";
            popupContent += "<tr>";
            popupContent += "<td><b>Desa</b></td>";
            popupContent += "<td>"+feature.properties.Desa+"</td>";
            popupContent += "</tr>";
            popupContent += "<td><b>Sungai</b></td>";
            popupContent += "<td>"+feature.properties.Sungai+"</td>";
            popupContent += "</tr>";
            popupContent += "<td><b>Kerusakan</b></td>";
            popupContent += "<td>"+feature.properties.Kerusakan+"</td>";
            popupContent += "</tr>";
            popupContent += "<td><b>Usulan Perbaikan</b></td>";
            popupContent += "<td>"+feature.properties.Usulan_Per+"</td>";
            popupContent += "</tr>";
            popupContent += "<td><b>Keterangan</b></td>";
            popupContent += "<td>"+feature.properties.Kerusakan1+"</td>";
            popupContent += "</tr>";
            popupContent += "</tbody>";
            popupContent += "</table>";
          }
          layer.bindPopup(popupContent);
        }
      });

      var bendungan = L.geoJSON(bendungan, {
        filter: function (feature, layer) {
          if (feature.properties) {
            // If the property "underConstruction" exists and is true, return false (don't render features under construction)
            return feature.properties.underConstruction !== undefined ? !feature.properties.underConstruction : true;
          }
          return false;
        },
        onEachFeature: function(feature,layer){
          var popupContent = "";
          if (feature.properties) {
            popupContent += "Waduk "+feature.properties.NAMA;
          }
          layer.bindPopup(popupContent);
        },
        color: '#808080'
      });

      var bendungan_on_going = L.geoJSON(bendungan_on_going, {
        filter: function (feature, layer) {
          if (feature.properties) {
            // If the property "underConstruction" exists and is true, return false (don't render features under construction)
            return feature.properties.underConstruction !== undefined ? !feature.properties.underConstruction : true;
          }
          return false;
        },
        onEachFeature: function(feature,layer){
          var popupContent = "";
          if (feature.properties) {
            popupContent += feature.properties.NAMA;
          }
          layer.bindPopup(popupContent);
        },
        color: 'black'
      });

      var embung = L.geoJSON(embung, {
        pointToLayer: function (feature, latlng) {
          return L.marker(latlng, {icon: embung_icon});
        },
        filter: function (feature, layer) {
          if (feature.properties) {
            // If the property "underConstruction" exists and is true, return false (don't render features under construction)
            return feature.properties.underConstruction !== undefined ? !feature.properties.underConstruction : true;
          }
          return false;
        },
        onEachFeature: function(feature,layer){
          var popupContent = "";
          if (feature.properties) {
            popupContent += "Embung "+feature.properties.EMBUNG;
          }
          layer.bindPopup(popupContent);
        },
        color: 'black'
      });

      var tanggul_pacitan = L.geoJSON(tanggul_pacitan, {
        pointToLayer: function (feature, latlng) {
          return L.marker(latlng, {icon: tanggul_icon});
        },
        filter: function (feature, layer) {
          if (feature.properties) {
            // If the property "underConstruction" exists and is true, return false (don't render features under construction)
            return feature.properties.underConstruction !== undefined ? !feature.properties.underConstruction : true;
          }
          return false;
        },
        onEachFeature: function(feature,layer){
          var popupContent = "";
          if (feature.properties) {
            popupContent += "<table border='2'>";
            popupContent += "<tbody>";
            popupContent += "<td colspan='2' class='text-center'><b>Tanggul Pacitan</b></td>";
            popupContent += "<tr>";
            popupContent += "<td><b>Desa</b></td>";
            popupContent += "<td>"+feature.properties.Desa+"</td>";
            popupContent += "</tr>";
            popupContent += "<td><b>Sungai</b></td>";
            popupContent += "<td>"+feature.properties.Sungai+"</td>";
            popupContent += "</tr>";
            popupContent += "<td><b>Kerusakan</b></td>";
            popupContent += "<td>"+feature.properties.Kerusakan+"</td>";
            popupContent += "</tr>";
            popupContent += "<td><b>Usulan Perbaikan</b></td>";
            popupContent += "<td>"+feature.properties.Usulan_Per+"</td>";
            popupContent += "</tr>";
            popupContent += "<td><b>Keterangan</b></td>";
            popupContent += "<td>"+feature.properties.Kerusakan1+"</td>";
            popupContent += "</tr>";
            popupContent += "</tbody>";
            popupContent += "</table>";
          }
          layer.bindPopup(popupContent);
        },
        color: 'black'
      });

      var baseLayers = {
        "Grayscale": grayscale,
        "Streets": streets
      };

      var overlays = {
        "Batas DAS": batas_das,
        "Tanggul Bojonegoro" : tanggul_bojonegoro,
        "Bendungan" : bendungan,
        "Bendungan on Going" : bendungan_on_going,
        "Embung" : embung,
        "Tanggul Pacitan" : tanggul_pacitan
      };

      L.control.layers(baseLayers,overlays,{collapsed: false}).addTo(map);

    </script>

    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
  </body>
</html>