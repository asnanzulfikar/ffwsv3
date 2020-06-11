"""
    map.py
    Aplikasi menampilkan Peta

    @author: Widoyo
    @date: 28 Nop 2017
"""
import datetime, time, json
import web
from sqlobject import AND, OR
from models import Agent, KLIMATOLOGI, WILAYAH, conn
from models import HIDROLOGI

urls = (
    '/curahhujan', 'MapCurahhujan',
    '/tma', 'MapTma',
    '/bendungan', 'MapBendungan',
    '/kualitasair','Ka'
)

app_map = web.application(urls, locals())
session = web.session.Session(app_map, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'role': None,
                                           'flash': None})
globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)


class MapCurahhujan:
    def GET(self):
        HIDE_THIS = [a.strip() for a in open('HIDE_ARR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == KLIMATOLOGI, Agent.q.AgentType == 0.0),
                                  Agent.q.expose == True))
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        sql = "SELECT prima_id, AgentName FROM agent WHERE AgentType IN (0, 1) AND LENGTH(prima_id)>4"
        try:
            rst = Agent._connection.queryAll(sql)
            all_prima = dict([(a[1].lower().replace('.', '_').replace(' ', '_'), a[0]) for a in rst])
        except:
            all_prima = {}
        #all_prima = dict(map(lambda x: (x[1], x[0]), [p.strip().split('\t') for p in open('PRIMA_ID.txt').readlines()]))
        all_pos = []
        for a in agents:
            sql = "SELECT Rain, CONCAT(SamplingDate, ' ', SamplingTime) AS sampling FROM %s ORDER BY SamplingDate DESC, SamplingTime DESC LIMIT 0, 1" % (a.table_name,)
            try:
                rst = Agent._connection.queryAll(sql)
            except:
                rst = None
            if rst:
                rain, sampling = rst[0]
                print(rst[0])
                sampling = datetime.datetime.strptime(sampling, '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() - sampling > datetime.timedelta(minutes=10):
                    rain = 0
                else:
                    rain = float(rain or 0)
            else:
                rain = 0
            p_ = {'id': a.AgentId, 'lrain': rain, 'name': a.cname, 'll': a.ll, 'tname': a.table_name,'petugas':[p.nama for p in a.petugas],'kode':[p.kode for p in a.petugas]}
            if a.table_name in all_prima.keys():
                p_.update({'device': all_prima.get(a.table_name)})
            all_pos.append(p_)
        js_foot = """
        <script type="text/template" id="pos_infowindow">
          <div class="item infowindow" id="pos_<%= index %>">
            <span class="pos"><%= name %> </span>
            <span class="meter">
            </span>
            <div class="">
              <ul>
                <li><i class="fa fa-bar-chart"></i> <a href="/curahhujan/<%= id %>">Hujan Tahunan</a></li>
                <li><i class="fa fa-calendar"></i> <a href="/curahhujan/<%= id %><% print('/' + sampling.split('-')[0] + '/' + sampling.split('-')[1]) %>">Hujan Bulan</a></li>
            </div>
          </div>
        </script>
        <script>
        var ws = new WebSocket('ws://mqtt.bbws-bsolo.net:22286');
        ws.onmessage = function (event) {
            var data = JSON.parse(event.data);
            if (data.device === undefined) { return; }
            var device_id = data.device.split('/')[1];
            var marker = undefined;
            for (m in markers) {
                if (markers[m].did == device_id) {
                    marker = markers[m].markerObj;
                    break;
                }
            }
            var icon_src = 'http://maps.google.com/mapfiles/ms/icons/green-dot.png';
            if (data.tick > 0) {
                // put did into rains_in
                var index = rains_in.indexOf(device_id);
                if (index == -1) {
                    rains_in.push(device_id);
                }
                icon_src = 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png';
                //icon_src = '/static/images/marker/gray_rain_2.gif';
            } else {
                var index = rains_in.indexOf(device_id);
                if (index > -1) {
                    rains_in.splice(device_id, 1);
                }

            }
            if (marker != undefined) {
                setIcon(marker, icon_src);
            }
        }
        var markers = [];
        var rains_in = [];
        var primaIds = """ + str(all_prima) + """;
        function setIcon(marker, icon_src='http://maps.google.com/mapfiles/ms/icons/green-dot.png') {
            marker.setIcon(icon_src);
        }
        function init_map() {
            var my_options = {
                center: new google.maps.LatLng(-7.49592,111.568909),
                zoom: 9,
                styles: [
    {
        "featureType": "all",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "weight": "2.00"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "geometry.stroke",
        "stylers": [
            {
                "color": "#9c9c9c"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "labels.text",
        "stylers": [
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "all",
        "stylers": [
            {
                "color": "#f2f2f2"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "landscape.man_made",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "poi",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "all",
        "stylers": [
            {
                "saturation": -100
            },
            {
                "lightness": 45
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#eeeeee"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#7b7b7b"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "road.highway",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "simplified"
            }
        ]
    },
    {
        "featureType": "road.arterial",
        "elementType": "labels.icon",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "transit",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "all",
        "stylers": [
            {
                "color": "#46bcec"
            },
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#88b6f2" /* "#c8d7d4" */
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#000000"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    }
],
                mapTypeId: google.maps.MapTypeId.TERRAIN };
            var map = new google.maps.Map(document.getElementById('map'), my_options);
            var batas_das = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/batas_das.kml',
                preserveViewport: true, map: map});

          var allPos = """ + str(all_pos) + """;
          var infoWindow = new google.maps.InfoWindow;
          _.each(allPos, function(pos) {
            var iw = `<div class="panel panel-default">
                <div class="panel-heading">
                <div class="panel-title"><h6>${pos.name}</h6></div></div>
                <div class="panel-body">
                <table class="table">
                <td>Prima ID</td><td>${pos.device}</td>
                </table>
                </div>
                <div class="panel-footer"><span class="glyphicon glyphicon-user"></span> ${pos.petugas} <b>${pos.kode}</b></div>
                </div>`
            var lat = parseFloat(pos.ll.split(',')[0]);
            var lng = parseFloat(pos.ll.split(',')[1]);
            var point = new google.maps.LatLng(lat, lng);
            var marker = new google.maps.Marker({
                icon: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
                map: map,
                optimized: false,
                title: pos.name + ' (' + pos.device + ')',
                position: point
            })
            markers.push({id: pos.id, did: pos.device, markerObj: marker});
            bind_info_window(marker, map, infoWindow, iw);
          });
        };
        function bind_info_window(marker, map, infowindow, html) {
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.setContent(html);
                infowindow.open(map, marker);
            })
        };
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAmnJGdC-ZhVd98H3mwMRv2GU2dlv1D7IA&callback=init_map"></script>
        """
        return render.map.curahhujan({'poses': agents, 'js_foot': js_foot})


class MapTma:
    def GET(self):
        HIDE_THIS = [a.strip() for a in open('HIDE_AWLR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == HIDROLOGI,
                                     Agent.q.AgentType == 0),
                                  Agent.q.expose == True)).orderBy(
                                      ["wilayah", "-DPL", "-siaga3"])
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        all_pos = []
        for a in agents:
            try:
                petugas = a.petugas[0].nama
                petugas_kode = a.petugas[0].kode
            except:
                petugas = '-'
                petugas_kode = '-'
            row = {'id': a.AgentId, 'name': a.cname, 'll': a.ll
                    ,'device':a.prima_id, 'petugas_nama': petugas,
                   'petugas_kode': petugas_kode} 
            all_pos.append(row)
        all_pos = json.dumps(all_pos)
        js_foot = """
        <script>
        var map;
        var dataLayer = [];
        var kmlSrc = [
            { title: 'Tanggul Pacitan', fname: 'tanggul_pacitan'},
            { title: 'Tanggul Bojonegoro', fname: 'tanggul_bojonegoro'},
            { title: 'Embung', fname: 'embung'},
            { title: 'Bendungan', fname: 'bendungan' },
            { title: 'Bendungan On Going', fname: 'bendungan_on_going'},
        ];
        function toggleKml(checked, id){
            if (checked){
                dataLayer[id].loadGeoJson('/static/gis/'+ kmlSrc[id].fname +'.json', {idPropertyName: kmlSrc[id].fname});
                dataLayer[id].setMap(map);
            } else {
                dataLayer[id].setMap(null);
            }
        }
        function init_map() {
            var my_options = {
                center: new google.maps.LatLng(-7.49592,111.568909),
                zoom: 9,
                styles: [
    {
        "featureType": "all",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "weight": "2.00"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "geometry.stroke",
        "stylers": [
            {
                "color": "#9c9c9c"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "labels.text",
        "stylers": [
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "all",
        "stylers": [
            {
                "color": "#f2f2f2"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "landscape.man_made",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "poi",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "all",
        "stylers": [
            {
                "saturation": -100
            },
            {
                "lightness": 45
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#eeeeee"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#7b7b7b"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "road.highway",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "simplified"
            }
        ]
    },
    {
        "featureType": "road.arterial",
        "elementType": "labels.icon",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "transit",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "all",
        "stylers": [
            {
                "saturation": 100
            },
            {
                "lightness": 15
            },
            {
                "color": "#88b6f2" /* "#466cec" */
            },
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#88b6f2"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#000000"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    }
],
                mapTypeId: google.maps.MapTypeId.TERRAIN };
            map = new google.maps.Map(document.getElementById('map'), my_options);
            var batas_das = new google.maps.KmlLayer(
                '/static/ws_bsolo_das.kml', {
                preserveViewport: true, map: map});

          var allPos = """ + str(all_pos) + """;
          var markers = {};
          var infoWindow = new google.maps.InfoWindow;
          let chk = "";
          for (let e in kmlSrc){
              dataLayer[e] = new google.maps.Data();
              chk += `<div class="checkbox"><label><input id="kml_${e}" onclick="toggleKml(this.checked, ${e})" type="checkbox" name="${kmlSrc[e].fname}">${kmlSrc[e].title}</label></div>`;
          };
          let ctrlForm = `<div class="panel panel-default"><div class="panel-body">
          <form style="font-size: 1.4rem;">
          ${chk}
          </form></div></div>`;
          var ctrlDiv = document.createElement('div');
          ctrlDiv.innerHTML = ctrlForm;
          map.controls[google.maps.ControlPosition.RIGHT_TOP].push(ctrlDiv);
          _.each(allPos, function(pos) {
            var iw = `<div class="panel panel-default">
                <div class="panel-heading">
                <div class="panel-title"><h6>${pos.name}</h6></div></div>
                <div class="panel-body">
                <table class="table">
                <td>Prima ID</td><td>${pos.device}</td>
                </table>
                </div>
                <div class="panel-footer"><span class="glyphicon
                glyphicon-user"></span>&nbsp;&nbsp;${pos.petugas_nama} <br>
                <span class="glyphicon glyphicon-barcode"></span>&nbsp;&nbsp;<b>${pos.petugas_kode}</b></div>
                </div>`
            var lat = parseFloat(pos.ll.split(',')[0]);
            var lng = parseFloat(pos.ll.split(',')[1]);
            var point = new google.maps.LatLng(lat, lng);
            var marker = new google.maps.Marker({
                icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                map: map,
                position: point
            });
            markers[pos.id] = marker;
            bind_info_window(marker, map, infoWindow, iw);
          });
        };
        function bind_info_window(marker, map, infowindow, html) {
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.setContent(html);
                infowindow.open(map, marker);
            })
        };
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAmnJGdC-ZhVd98H3mwMRv2GU2dlv1D7IA&callback=init_map"></script>
        """
        return render.map.tma({'poses': agents, 'js_foot': js_foot})

class Ka:
    def GET(self):
        conn = Agent._connection

        #sql = "select k.waktu,k.ip,k.id_pos,a.cname,a.ll from kualitas_air k inner join (SELECT MAX(c.waktu) as max_date, c.ip, d.id,d.cname,d.ll FROM kualitas_air c, lokasi d WHERE c.id_pos=d.id GROUP BY d.id) a on a.max_date = k.waktu and a.id = k.id_pos order by k.id_pos ASC"
        sql = "select k.waktu,k.ip,k.id_pos,a.cname,a.ll,a.show from kualitas_air k inner join (SELECT MAX(c.waktu) as max_date, c.ip, d.id,d.cname,d.ll,d.show FROM kualitas_air c, lokasi d WHERE c.id_pos=d.id GROUP BY d.id) a on a.max_date = k.waktu and a.id = k.id_pos and a.show = 1 order by k.id_pos ASC"
        rst = conn.queryAll(sql)
        all_pos=[]
        for ka in rst:
            a = ka[0].strftime("%b %Y")
            if ka[1] == None:
                ip_last_time = "Belum Tersedia"
            else:
                ip_last_time = ka[1]
            all_pos.append({'id': str(ka[2]), 'name': ka[3], 'll': ka[4],'last_time':a,'ip_last_time':ip_last_time})
        js_foot = """
        <script type="text/template" id="pos_infowindow">
          <div class="item infowindow" id="pos_<%= index %>">
            <span class="pos"><%= name %> </span>
            <span class="meter">
            </span>
          </div>
        </script>
        <script>

        function init_map() {
            var my_options = {
                center: new google.maps.LatLng(-7.49592,111.568909),
                zoom: 9,
                styles: [
                            {
                                "featureType": "all",
                                "elementType": "geometry.fill",
                                "stylers": [
                                    {
                                        "weight": "2.00"
                                    }
                                ]
                            },
                            {
                                "featureType": "all",
                                "elementType": "geometry.stroke",
                                "stylers": [
                                    {
                                        "color": "#9c9c9c"
                                    }
                                ]
                            },
                            {
                                "featureType": "all",
                                "elementType": "labels.text",
                                "stylers": [
                                    {
                                        "visibility": "on"
                                    }
                                ]
                            },
                            {
                                "featureType": "landscape",
                                "elementType": "all",
                                "stylers": [
                                    {
                                        "color": "#f2f2f2"
                                    }
                                ]
                            },
                            {
                                "featureType": "landscape",
                                "elementType": "geometry.fill",
                                "stylers": [
                                    {
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "featureType": "landscape.man_made",
                                "elementType": "geometry.fill",
                                "stylers": [
                                    {
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "featureType": "poi",
                                "elementType": "all",
                                "stylers": [
                                    {
                                        "visibility": "off"
                                    }
                                ]
                            },
                            {
                                "featureType": "road",
                                "elementType": "all",
                                "stylers": [
                                    {
                                        "saturation": -100
                                    },
                                    {
                                        "lightness": 45
                                    }
                                ]
                            },
                            {
                                "featureType": "road",
                                "elementType": "geometry.fill",
                                "stylers": [
                                    {
                                        "color": "#eeeeee"
                                    }
                                ]
                            },
                            {
                                "featureType": "road",
                                "elementType": "labels.text.fill",
                                "stylers": [
                                    {
                                        "color": "#7b7b7b"
                                    }
                                ]
                            },
                            {
                                "featureType": "road",
                                "elementType": "labels.text.stroke",
                                "stylers": [
                                    {
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "featureType": "road.highway",
                                "elementType": "all",
                                "stylers": [
                                    {
                                        "visibility": "simplified"
                                    }
                                ]
                            },
                            {
                                "featureType": "road.arterial",
                                "elementType": "labels.icon",
                                "stylers": [
                                    {
                                        "visibility": "off"
                                    }
                                ]
                            },
                            {
                                "featureType": "transit",
                                "elementType": "all",
                                "stylers": [
                                    {
                                        "visibility": "off"
                                    }
                                ]
                            },
                            {
                                "featureType": "water",
                                "elementType": "all",
                                "stylers": [
                                    {
                                        "saturation": 100
                                    },
                                    {
                                        "lightness": 15
                                    },
                                    {
                                        "color": "#88b6f2" /* "#466cec" */
                                    },
                                    {
                                        "visibility": "on"
                                    }
                                ]
                            },
                            {
                                "featureType": "water",
                                "elementType": "geometry.fill",
                                "stylers": [
                                    {
                                        "color": "#88b6f2"
                                    }
                                ]
                            },
                            {
                                "featureType": "water",
                                "elementType": "labels.text.fill",
                                "stylers": [
                                    {
                                        "color": "#000000"
                                    }
                                ]
                            },
                            {
                                "featureType": "water",
                                "elementType": "labels.text.stroke",
                                "stylers": [
                                    {
                                        "color": "#ffffff"
                                    }
                                ]
                            }
                        ],
                    

        mapTypeId: google.maps.MapTypeId.TERRAIN };
        var map = new google.maps.Map(document.getElementById('map'), my_options);
        var batas_das = new google.maps.KmlLayer(
            {url: 'http://hidrologi.bbws-bsolo.net/static/batas_das.kml',
            preserveViewport: true, map: map});

        /*
        var s_bengawan_solo = new google.maps.KmlLayer(
            {url: 'http://hidrologi.bbws-bsolo.net/static/s_bengawan_solo.kml',
            preserveViewport: true, map: map});
        */

        var icons = {
          memenuhi_mutu_baku: {
            name: 'Memenuhi Mutu Baku',
            icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
          },
          cemar_ringan: {
            name: 'Cemar Ringan',
            icon: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'
          },
          cemar_sedang: {
            name: 'Cemar Sedang',
            icon: 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png'
          },
          cemar_berat: {
            name: 'Cemar Berat',
            icon: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
          }
        };

        var legend = document.getElementById('legend');
        for (var key in icons) {
          var type = icons[key];
          var name = type.name;
          var icon = type.icon;
          var div = document.createElement('div');
          div.innerHTML = '<img src="' + icon + '"> ' + name;
          legend.appendChild(div);
        }

        map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(legend);


          var allPos = """ + str(all_pos) + """;
          var markers = {};
          var infoWindow = new google.maps.InfoWindow;
          _.each(allPos, function(pos) {
            if(pos.ip_last_time <= 1){
                    var icon = 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png';
            }else if(pos.ip_last_time > 1 && pos.ip_last_time <= 5){
                    var icon = 'http://maps.google.com/mapfiles/ms/icons/green-dot.png';
            }else if(pos.ip_last_time > 5 && pos.ip_last_time <= 10){
                    var icon = 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png';
            }else if(pos.ip_last_time > 10){
                    var icon = 'http://maps.google.com/mapfiles/ms/icons/red-dot.png';
            }else{
                var icon = 'http://maps.google.com/mapfiles/ms/icons/orange-dot.png';
            }
            var lat = parseFloat(pos.ll.split(',')[0]);
            var lng = parseFloat(pos.ll.split(',')[1]);
            var point = new google.maps.LatLng(lat, lng);
            var marker = new google.maps.Marker({
                icon:icon,
                map: map,
                position: point
            });
            markers[pos.id] = marker;
            bind_info_window(marker, map, infoWindow, "<a href='/kualitasair/chart/"+pos.id+"' style='font-weight: bold;font-size: 16px;'>"+ pos.name + "</a>"+"<br>"+"Data Terakhir : "+pos.last_time+"<br>"+"IP Terakhir : "+pos.ip_last_time);
          });
        };
        function bind_info_window(marker, map, infowindow, html) {
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.setContent(html);
                infowindow.open(map, marker);
            })
        };
        </script>
        
        <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAmnJGdC-ZhVd98H3mwMRv2GU2dlv1D7IA&callback=init_map"></script>
        """

        return render.map.kualitasair({'js_foot': js_foot})
