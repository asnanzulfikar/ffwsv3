import datetime
import time
import re
import web
import json
import decimal

import psycopg2 as pg
from sqlobject import AND, OR

from models import TinggiMukaAir, CurahHujan
from models import Agent, conn, HIDROLOGI, KLIMATOLOGI
from helper import to_date
from common_data import BSOLO_LOGGER

urls = (
    '$', 'Api',
    '/sensor', 'Sensor',  # List of incoming device(s)
    '/sensor/(.*)', 'Sensor',  # Showing single device
    '/curahhujan', 'CurahHujanApi', # curah hujan telemetri&manual
    '/chcustom','CHCustom', # api ch untuk kebutuhan olah data custom staff hidrologi
    '/tma', 'Tma', # Data TMA serupa /tma
    '/tmax', 'Tmax',
    '/graph/(.*)', 'SensorGraph',  # Showing single device graph
    '/logger', 'BsoloLogger',  # List of registered logger
    '/agentch','AgentCH'
)

app_api = web.application(urls, locals())
session = web.session.Session(app_api, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'role': None,
                                           'flash': None})
globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)



def json_serialize(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError ("Type %s not serializable" % type(obj))

class AgentCH():
    def GET(self):
        HIDE_THIS = [a.strip() for a in open('HIDE_ARR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == KLIMATOLOGI, Agent.q.AgentType == 0.0), Agent.q.expose == True)).orderBy(('wilayah', 'urutan', ))
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        data = []
        for a in agents:
            row = {'pos':a.cname or a.AgentName,'table_name':a.table_name,'pos_id':a.AgentId}
            data.append(row)
        return json.dumps(data, default=json_serialize)

class CurahHujanApi():
    def GET(self):
        tanggal = web.input().get('d')
        if not tanggal:
            tanggal = datetime.date.today() - datetime.timedelta(days=1)
        else:
            try:
                tanggal = to_date(tanggal)
            except:
                tanggal = to_date(tanggal)
        HIDE_THIS = [a.strip() for a in open('HIDE_ARR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == KLIMATOLOGI, Agent.q.AgentType == 0.0), Agent.q.expose == True)).orderBy(('wilayah', 'urutan', ))
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        data = []
        for a in agents:
            rain = a.get_segmented_rain(tanggal)
            row = {'pos': a.cname or a.AgentName, 'id': a.AgentId,
                   'telemetri': rain.get('total'), 'manual': rain.get('manual')}
            data.append(row)
        return json.dumps({'tanggal': tanggal, 'curahhujan': data}, default=json_serialize)


class CHCustom():
    def GET(self):
        tanggalmin = web.input().get('tanggalmin')
        tanggalmax = web.input().get('tanggalmax')
        pos_ch = web.input().get('pos_ch')
        if not tanggalmin or not tanggalmax:
            return json.dumps({'response':'pilih tanggal minimal dan tanggal maksimal untuk rentang waktu'})
        else:
            tanggalmin = tanggalmin.replace('/','-')
            tanggalmax = tanggalmax.replace('/','-')
            data=[]
            alldata = Agent._connection.queryAll("SELECT SamplingDate,SamplingTime,Rain FROM {0} WHERE SamplingDate BETWEEN '{1}' and '{2}' and Rain > 0".format(str(pos_ch),tanggalmin,tanggalmax))
            for a in alldata:
                row={'SamplingDate':a[0],'SamplingTime':str(a[1]),'Rain':a[2]}
                data.append(row)
            return json.dumps(data, default=json_serialize)


class Tma():
    def GET(self):
        tanggal = web.input().get('d')
        if not tanggal:
            tanggal = datetime.date.today()
        else:
            try:
                tanggal = datetime.datetime.strptime(tanggal, "%Y-%m-%d").date()
            except:
                tanggal = datetime.datetime.strptime(tanggal, "%d %b %y").date()
        HIDE_THIS = [a.strip() for a in open('HIDE_AWLR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == HIDROLOGI,
                                     Agent.q.AgentType == 0),
                                  Agent.q.expose == True)).orderBy(
                                      ["wilayah", "urutan"])
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        data = []
        for a in agents:
            tma = a.get_segmented_wl(tanggal)
            segments = ('pagi', 'siang', 'sore')
            row = {'pos': a.cname, 'id': a.AgentId, 'dpl': a.DPL}
            for s in segments:
                row.update({s: {'manual': tma[s].manual, 'telemetri':
                                tma[s].telemetri}})
            data.append(row)
        return json.dumps({'tanggal': tanggal, 'tma': data}, default=json_serialize)


class Tmax():
    def GET(self):
        data=[]
        alldata = Agent._connection.queryAll("SELECT waktu,jam,manual,origin FROM tma WHERE YEAR(waktu)=2020 AND agent_id=2 ORDER BY waktu,jam")
        for a in alldata:
            row={'waktu':a[0],'jam':a[1],'manual':a[2],'origin':a[3]}
            data.append(row)
        return json.dumps(data, default=json_serialize)


def ts(x):
    try:
        return datetime.datetime.fromtimestamp(x).isoformat()
    except ValueError:
        return datetime.datetime.fromtimestamp(0).isoformat()


def map_periodic(src):
    try:
        loc = BSOLO_LOGGER.get(src.get('device').split('/')[1])
    except KeyError:
        loc = src.get('device').split('/')[1]
    data_keys = "tick;distance;wl_scale;wlevel;temperature_ambien_scale;humidity_ambien_scale;wind_speed_scale;wind_dir_scale;sun_radiation_scale".split(';')
    ret = {"up_since": ts(src.get('up_since') or 0),
            "sampling": ts(src.get('sampling') or 0),
            "time_set_at": ts(src.get("time_set_at") or 0),
            "temperature": src.get("temperature"),
            "humidity": src.get("humidity"),
            "signal_quality": src.get("signal_quality"),
            "battery": src.get("battery", None),
            "pressure": src.get("pressure", None),
            "altitude": src.get("altitude", None),
            "location": loc}
    for i in data_keys:
        if i in src:
            ret.update({i: src.get(i)})
    return ret




class BsoloLogger:
    ''''''
    def GET(self):
        '''Show List of registered logger'''
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')
        pos_selected = Agent.select(AND(Agent.q.prima_id != None, OR(Agent.q.AgentType == 0, Agent.q.AgentType == 1, Agent.q.AgentType == 2, Agent.q.AgentType == 3)))
        wi = web.input()
        if wi.get('type', None):
            pos_selected = [a for a in pos_selected if a.AgentType == int(wi.get('type'))]
        rst = [{'type': a.AgentType, 'cname': a.cname,
            'lonlat': a.ll, 'dpl': a.DPL, 'prima_id': a.prima_id,
            'tinggi_sonar': a.tinggi_sonar,
            'tipping_factor': a.TippingFactor} for a in pos_selected if len(a.prima_id) > 4]
        return json.dumps(rst)


class Sensor:
    '''Get Periodic data or device properties'''
    def get_periodic(self, device, sampling=None):
        '''Return list of periodic data this device, filter by sampling date'''
        pass

    def GET(self, did=None):
        '''@params:
            did: (str)device id
            sampling: (datetime'''
        conn = pg.connect(dbname="bsolo3", user="bsolo3", password="4545-id")
        cursor = conn.cursor()

        web.header('Content-Type', 'text/json')
        web.header('Access-Control-Allow-Origin', '*')
        if did:
            sql = "SELECT content FROM raw WHERE content->>'device' LIKE %s ORDER BY id DESC LIMIT 35"
            cursor.execute(sql, ('%/' + did + '/%',))
            '''
            regx = re.compile('.*'+did+'/', re.IGNORECASE)
            rst = [r for r in db.sensors.find({"device": regx},
                                                {"_id": 0}).sort(
                                                    "_id", -1).limit(25)]
            '''
            rst = [r[0] for r in cursor.fetchall()]
            if not rst:
                return web.notfound()
            if web.input().get('sampling', None):
                #try:
                sampling = to_date(web.input().get('sampling'))
                _dari = time.mktime(sampling.timetuple())
                _hingga = _dari + 86400
                    # satu hari = 86400 ms
                '''
                    rst = [r for r in db.sensors.find(
                        {"$and": [{"device": regx},
                                  {"sampling": {"$gte": _dari}},
                                  {"sampling": {"$lt": _hingga}}]}, {_id: 0})]
                '''
                sql = "SELECT content FROM raw WHERE content->>'device' LIKE %s AND (content->>'sampling')::int >= %s AND (content->>'sampling')::int <= %s"
                cursor.execute(sql, ('%/' + did + '/%', _dari, _hingga))
                rst = [r[0] for r in cursor.fetchall()]
                #except Exception as e:
                #    print e
            out = {}
            if web.input().get('raw'):
                out['periodic'] = rst
            else:
                out['periodic'] = [map_periodic(r) for r in rst]
            out["bsolo_logger"] = BSOLO_LOGGER.get(did)
        else:
            out = []
            sql = "SELECT DISTINCT(content->>'device') FROM raw"
            cursor.execute(sql)
            out = [r[0] for r in cursor.fetchall()]
        cursor.close()
        conn.close()

        return json.dumps(out)


class SensorGraph:
    def GET(self, did=None):
        '''@params:
            did: (str)device id
            sampling: (datetime'''
        conn = pg.connect(dbname="bsolo3", user="bsolo3", password="4545-id")
        cursor = conn.cursor()

        if did:
            sql = "SELECT content FROM raw WHERE content->>'device' LIKE %s ORDER BY id DESC LIMIT 35"
            cursor.execute(sql, ('%/' + did + '/%',))
            '''
            regx = re.compile('.*'+did+'/', re.IGNORECASE)
            rst = [r for r in db.sensors.find({"device": regx},
                                                {"_id": 0}).sort(
                                                    "_id", -1).limit(25)]
            '''
            rst = [r[0] for r in cursor.fetchall()]
            if not rst:
                return web.notfound()
            if web.input().get('sampling', None):
                #try:
                sampling = to_date(web.input().get('sampling'))
                _dari = time.mktime(sampling.timetuple())
                _hingga = _dari + 86400
                    # satu hari = 86400 ms
                '''
                    rst = [r for r in db.sensors.find(
                        {"$and": [{"device": regx},
                                  {"sampling": {"$gte": _dari}},
                                  {"sampling": {"$lt": _hingga}}]}, {_id: 0})]
                '''
                sql = "SELECT content FROM raw WHERE content->>'device' LIKE %s AND (content->>'sampling')::int >= %s AND (content->>'sampling')::int <= %s"
                cursor.execute(sql, ('%/' + did + '/%', _dari, _hingga))
                rst = [r[0] for r in cursor.fetchall()]
                if not rst:
                    return "Tidak Ada Data Pada Tanggal " + web.input().get('sampling')
                rst.reverse()
                #except Exception as e:
                #    print e
            out = {}
            if web.input().get('raw'):
                out['periodic'] = rst
            else:
                out['periodic'] = [map_periodic(r) for r in rst]
            out["bsolo_logger"] = BSOLO_LOGGER.get(did)
        else:
            out = []
            sql = "SELECT DISTINCT(content->>'device') FROM raw"
            cursor.execute(sql)
            out = [r[0] for r in cursor.fetchall()]
        cursor.close()
        conn.close()


        #testing from asnan (data untuk kategori grafik) tinggal return untuk melihat
        data=[]
        kategori = []
        battery = []
        signal_quality = []
        tick = []
        are_tick = False
        distance = []
        are_distance = False
        wl_scale = []
        are_wl_scale = False

        sun_radiation_scale = []
        wind_dir_scale =[]
        temperature_ambien_scale = []
        humidity_ambien_scale = []
        wind_speed_scale =[]
        are_klimatologi = False

        r = out["periodic"]
        r.reverse()

        for j in r:
            if "distance" in j:
                are_distance = True
                distance.append(j.get("distance"))
            if "wl_scale" in j:
                are_wl_scale = True
                wl_scale.append(j.get("wl_scale"))
            if "tick" in j:
                if "sun_radiation_scale" and "wind_dir_scale" and "temperature_ambien_scale" and "humidity_ambien_scale" and "wind_speed_scale" in j:
                    are_klimatologi = True
                    sun_radiation_scale.append(j.get("sun_radiation_scale"))
                    wind_dir_scale.append(j.get("wind_dir_scale"))
                    temperature_ambien_scale.append(j.get("temperature_ambien_scale"))
                    humidity_ambien_scale.append(j.get("humidity_ambien_scale"))
                    wind_speed_scale.append(j.get("wind_speed_scale"))
                    tick.append(j.get("tick"))
                else:
                    are_tick = True
                    tick.append(j.get("tick"))

            kategori.append(j.get("sampling"))
            battery.append(j.get("battery"))
            signal_quality.append(j.get("signal_quality"))
        #end
        data.append({'name':'signal_quality','data':signal_quality})
        data.append({'name':'battery','data':battery})
        if are_distance == True:
            data.append({'name':'distance','data':distance})
            jenis_prima = "SONAR"
        if are_wl_scale == True:
            data.append({'name':'wl_scale','data':wl_scale})
            jenis_prima = "PRESSURE"
        if are_tick == True:
            data.append({'name':'tick','data':tick})
            jenis_prima = "ARR"
        if are_klimatologi == True:
            data.append({'name':'tick','data':tick})
            data.append({'name':'sun_radiation_scale','data':sun_radiation_scale})
            data.append({'name':'wind_dir_scale','data':wind_dir_scale})
            data.append({'name':'temperature_ambien_scale','data':temperature_ambien_scale})
            data.append({'name':'humidity_ambien_scale','data':humidity_ambien_scale})
            data.append({'name':'wind_speed_scale','data':wind_speed_scale})
            jenis_prima = "KLIMATOLOGI"

        conn = Agent._connection
        sql = "SELECT cname from agent where prima_id = %s" % ('"'+did+'"')
        result = conn.queryAll(sql)
        if result:
            pname = result[0][0]
        else:
            pname = "--"
        #print result

        return render.sensor.sensor_graph({'data':str(data),'kategori':str(kategori),'did':did,'jenis_prima':jenis_prima,'pname':pname})
        #return out["periodic"]
        


class Api:
    def GET(self):
        return json.dumps({'a': 'Hello World!'})

    def post_ch(self, data):
        data["obj"]["mtime_manual"] = datetime.datetime.strptime(
            data["obj"]["mtime_manual"][0:19], "%Y-%m-%dT%H:%M:%S")
        data["obj"]["waktu"] = datetime.datetime.strptime(
            data["obj"]["waktu"], "%Y-%m-%d")
        try:
            ch = CurahHujan.selectBy(agentID=data["obj"]["agentID"],
                                     waktu=data["obj"]["waktu"])[0]
            ch.manual = data["obj"]["manual"]
            ch.syncUpdate()
        except IndexError:
            CurahHujan(**data["obj"])

    def post_tma(self, data):
        mtime = data["obj"]["mtime"][0:19]
        data["obj"]["mtime"] = datetime.datetime.strptime(mtime,
                                                          "%Y-%m-%dT%H:%M:%S")
        data["obj"]["waktu"] = datetime.datetime.strptime(data["obj"]["waktu"],
                                                          "%Y-%m-%d")
        try:
            # periksa jika data sudah ada sebelumnya, lakukan UPDATE
            tma = TinggiMukaAir.selectBy(agentID=data["obj"]["agentID"],
                                         jam=data["obj"]["jam"],
                                         waktu=data["obj"]["waktu"])[0]
            tma.manual = data["obj"]["manual"]
            tma.syncUpdate()
        except IndexError:
            TinggiMukaAir(**data["obj"])

    def post_waduk_daily(self, data):
        data["obj"]["waktu"] = datetime.datetime.strptime(
            data["obj"]["waktu"], "%Y-%m-%d")
        try:
            wd = WadukDaily.selectBy(posID=data["obj"]["posID"],
                                     waktu=data["obj"]["waktu"])[0]
            wd.elevasi = data["obj"]["elevasi"]
            wd.volume = data["obj"]["volume"]
            wd.rembesan = data["obj"]["rembesan"]
            wd.curahhujan = data["obj"]["curahhujan"]
            wd.mtime = datetime.datetime.now()
        except IndexError:
            WadukDaily(**(data["obj"]))

    def post_flow(self, data):
        data["obj"]["waktu"] = datetime.datetime.strptime(
            data["obj"]["waktu"], "%Y-%m-%d")
        try:
            flow = Flow.selectBy(gateID=data["obj"]["gateID"],
                                 waktu=data["obj"]["waktu"])[0]
            flow.opened = data["obj"]["opened"]
            flow.timed = data["obj"]["timed"]
            flow.value = data["obj"]["value"]
            # flow autosave, karena tidak 'lazyUpdate'
        except IndexError:
            Flow(**data["obj"])

    def POST(self):
        web.header('Content-Type', 'text/json')
        web.header('Access-Control-Allow-Origin', '*')
        data = json.loads(web.data())
        if data["meta"]["table"] == "tma":
            self.post_tma(data)
        if data["meta"]["table"] == "curahhujan":
            self.post_ch(data)
        if data["meta"]["table"] == "flow":
            self.post_flow(data)
        if data["meta"]["table"] == "waduk_daily":
            self.post_waduk_daily(data)
        return json.dumps({"Ok": True})

class MTinggiMukaAir:
    '''Untuk mengambil data tma yang dikirim petugas'''
    def GET(self):
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')
        inp = web.input()
        sampling = inp.get('sampling')
        n = datetime.datetime.now()
        waktu = n.replace(hour=0, minute=0, second=0, microsecond=0).date()
        if sampling:
            d = to_date(sampling)
            waktu = datetime.datetime(d.year, d.month, d.day).date()
        rst = [c.sqlmeta.asDict() for c in
               TinggiMukaAir.select(TinggiMukaAir.q.waktu==waktu)]
        return json.dumps(rst, default=json_serialize)



class MCurahHujan:
    '''Untuk mengambil data curahhujan yang dikirim petugas'''
    def GET(self):
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')
        inp = web.input()
        sampling = inp.get('sampling')
        n = datetime.datetime.now()
        waktu = n.replace(hour=0, minute=0, second=0, microsecond=0).date()
        if sampling:
            d = to_date(sampling)
            waktu = datetime.datetime(d.year, d.month, d.day).date()
        rst = [c.sqlmeta.asDict() for c in
               CurahHujan.select(CurahHujan.q.waktu==waktu)]
        return json.dumps(rst, default=json_serialize)


