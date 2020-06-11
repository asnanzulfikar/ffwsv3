# Data Management
import sys
import datetime
import calendar
import json
sys.path.append('../')

#from collections import OrderedDict

import web
from sqlobject import OR, AND, SQLObjectNotFound
from sqlobject import *
import paho.mqtt.publish as publish

MQTT_HOST = 'mqtt.bbws-bsolo.net'
MQTT_PORT = 14983
MQTT_TOPIC = 'data_manual'

from models import AgentCh, Agent, AgentTma, conn, Authuser, TinggiMukaAir
from models import CurahHujan, KlimatManual
from models import Petugas

from adm.user import adm_user
from adm.curahhujan import adm_ch

from helper import to_date, json_serializer

urls = (
    '', 'Index',
    '/ch', adm_ch, #'ChIndex',
    '/tma', 'TmaIndex',
    '/tma/update', 'TMAUpdate',
    '/tma/(\w+\.*\-*\w+)', 'TmaShow',
    '/user', 'Users',
    '/petugas','DataPetugas',
    '/klimatologi/update', 'KlimatUpdate',
    '/klimatologi/(\w+\.*\-*\w+)', 'KlimatShow',
)


app_adm = web.application(urls, locals())
session = web.session.Session(app_adm, web.session.DiskStore('sessions'),
        initializer={'username': None, 'is_admin': None,
            'table_name': None, 'err': None})

def csrf_token():
    if not session.has_key('csrf_token'):
        from uuid import uuid4
        session['csrf_token'] = uuid4().hex
    return session.get('csrf_token')


globals = {'session': session, 'csrf_token': csrf_token}
render = web.template.render('templates/', base='base_adm', globals=globals)

class DataPetugas:
    def GET(self):
        petugas = Petugas.select()
        return render.adm.petugas.petugas({'petugas': petugas})

def pub_object(obj):
    if type(obj) == TinggiMukaAir:
        what = 'tma'
    elif type(obj) == CurahHujan:
        what = 'ch'
    data = json.dumps(dict(meta={'what': what}, object=obj.sqlmeta.asDict()), default=json_serializer)
    publish.single(MQTT_TOPIC, payload=data, hostname=MQTT_HOST, port=MQTT_PORT)


def csrf_protected(func):
    def decorated(*args, **kwargs):
        inp = web.input()
        print('CSRF_TOKEN', inp.csrf_token)
        print('SESSION_CSRF_TOKEN', session.get('csrf_token'))
        if not (inp.has_key('csrf_token') and inp.csrf_token==session.pop('csrf_token', None)):
            raise web.HTTPError(
                    '400 Bad Request',
                    {'content-type': 'text/html'},
                    """Cross-site request forgery (CSRF) attempt (or stale browser form, <a href='#'>Kembali</a>""")
        return func(*args, **kwargs)
    return decorated


def get_tma_daily_on_pos(pos, today=datetime.date.today()):
    pos = [a for a in AgentTma.select(OR(AgentTma.q.AgentType==2,AgentTma.q.AgentType==0)) if a.table_name == pos][0]
    sql = "SELECT waktu, jam, manual, id FROM tma WHERE agent_id=%s AND YEAR(waktu)=%s AND MONTH(waktu)=%s ORDER BY waktu, CAST(jam AS SIGNED)" % (pos.id, today.year, today.month)
    rs = conn.queryAll(sql)
    out = []
    t = None
    rows = {}
    for r in rs:
        jam = len(r[1]) == 1 and '0' + r[1] or r[1]
        if t != r[0]:
            rows[r[0]] = {jam: {'lokal': {'lokal': r[2], 'id': r[3]}, 'ttg': r[2] + pos.DPL, 'id': r[3]}}
            
            t = r[0]
            next
        rows[t].update({jam: {'lokal': {'lokal': r[2], 'id': r[3]}, 'ttg': r[2] + pos.DPL, 'id': r[3]}})
    return rows


def login_required(func):
    def func_wrapper(*args, **kwargs):
        if not session.get('username'):
            raise web.seeother('/login', absolute=True)
        return func(*args, **kwargs)
    return func_wrapper


def admin_required(func):
    def func_wrapper(*args, **kwargs):
        if session.get('table_name'):
            raise web.forbidden()
        return func(*args, **kwargs)
    return func_wrapper


class ChIndex:
    @login_required
    @admin_required
    def GET(self):
        return render.adm.ch.index()


class KlimatShow:
    @login_required
    def GET(self, table_name):
        '''Masuk ke sini jika authuser.is_admin == 4'''
        agent_id = dict([a.split('\t') for a in open('agent_table.txt').readlines()]).get(table_name)
        pos = Agent.get(agent_id)
        webinput = web.input(sampling=str(datetime.date.today() - datetime.timedelta(days=1)))
        tg = datetime.datetime.strptime(webinput.sampling, '%Y-%m-%d').date()
        rst = KlimatManual.select(AND(func.YEAR(KlimatManual.q.sampling)==tg.year, 
            func.MONTH(KlimatManual.q.sampling)==tg.month, KlimatManual.q.agent==agent_id))
            
        return render.adm.klimatologi.show({'tg': tg, 'pos': pos, 'data': rst})

    def POST(self, table_name):
        agent_id = dict([a.split('\t') for a in open('agent_table.txt').readlines()]).get(table_name)
        pos = Agent.get(agent_id)
        try:
            pos = [a for a in AgentCh.select(AgentCh.q.AgentType==1) if a.table_name == table_name][0]
        except IndexError:
            return web.notfound()
        inp = web.input()
        float_list = 'ch_m,temp_min_m,temp_max_m,humi_m,kec_angin_m,penguapan_m'.split(',')
        for kol in float_list:
            if inp.get(kol):
                inp.update({kol: float(inp.get(kol))})
            else:
                inp.update({kol: None})

        inp.update({'penyinaran_m': inp.get('penyinaran_m') and int(inp.get('penyinaran_m')) or None})
        inp.update({'agentID': pos.id, 'cuser': session.username, 'cdate': datetime.datetime.now()})
        inp.update({'sampling': to_date(inp.get('sampling'))})
        if 'csrf_token' in inp:
            del inp['csrf_token']
        rst = KlimatManual.select(AND(KlimatManual.q.agent==pos, 
                func.DATE(KlimatManual.q.sampling)==inp.get('sampling')))
        if rst.count():
            rst[0].set(**inp)
        else:
            km = KlimatManual(**inp)

        # table curahhujan perlu ditambah/update
        ch = CurahHujan.select(AND(CurahHujan.q.agent==pos,
            func.DATE(CurahHujan.q.waktu) == inp.get('sampling')))
        if ch.count():
            ch[0].set(**{'manual': float(inp.get('ch_m', 0))})
        else:
            ch = CurahHujan(**{'waktu': inp.get('sampling'), 
                'manual': float(inp.get('ch_m', 0)), 'agent': pos})
        return web.redirect('/adm/klimatologi/' + table_name, absolute=True)



class KlimatUpdate:
    @login_required
    def POST(self):
        inp = web.input()
        try:
            km = KlimatManual.get(int(inp.get('pk')))
            km.set(**{inp.get('name'): float(inp.get('value',0))})
            km.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        if inp.get('name') == 'ch_m':
            ch = CurahHujan.select(AND(CurahHujan.q.agent==km.agent,
                CurahHujan.q.waktu == km.sampling.date()))
            if ch.count():
                ch[0].set(**{'manual': float(inp.get('value', 0))})
                ch[0].syncUpdate()
            else:
                ch = CurahHujan(**{'waktu': km.sampling, 
                    'manual': float(inp.get('value', 0)), 'agent': km.agent})


        return {"Ok": "true"}


class TmaShow:
    @login_required
    def GET(self, table_name):
        pos = [a for a in AgentTma.select(OR(AgentTma.q.AgentType==2, AgentTma.q.AgentType==0)) if a.table_name == table_name][0]
        webinput = web.input(sampling=str(datetime.date.today()))
        tg = datetime.datetime.strptime(webinput.sampling, '%Y-%m-%d').date()
        rs = get_tma_daily_on_pos(pos.table_name, tg)
        ordered_date = sorted(rs.keys(), reverse=True)
        print(pos)
        print('')
        print(rs)
        print('')
        print(ordered_date)
        print('')
        print(tg)
        return render.adm.tma.show_editable({'pos': pos, 'data': rs, 'dated': ordered_date, 'tg': tg})

    @login_required
    def POST(self, table_name):
        try:
            pos = [a for a in AgentTma.select(AgentTma.q.AgentType==2) if a.table_name == table_name][0]
        except IndexError:
            return web.notfound()
        inp = web.input()
        sql = "SELECT id FROM tma WHERE agent_id=%s AND waktu='%s' AND jam='%s'" % (pos.id, to_date(inp.waktu), inp.jam)
        rs = conn.queryAll(sql)
        print('pos.id: ', pos.id)
        if pos.id >= 200 and pos.id not in [231, 233, 237, 238, 239]:
            inp_manual = float(inp.tma) - pos.DPL
        else:
            inp_manual = float(inp.tma)
        print(pos.sqlmeta.asDict())
        if not rs:
            tma = TinggiMukaAir(agent=pos, waktu=to_date(inp.waktu), jam=inp.jam, manual=inp_manual)
            pub_object(tma)
        return web.redirect('/adm/tma/' + table_name, absolute=True)


class TMAUpdate:
    @login_required
    def POST(self):
        inp = web.input()
        try:
            tma = TinggiMukaAir.get(int(inp.get('pk')))
            tma.set(**{inp.get('name'): float(inp.get('value',0))})
            tma.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}

class Users:
    @login_required
    @admin_required
    def GET(self):
        users = Authuser.select()
        return render.adm.users.index({'users': users})


class Dummy(object):
    pass

class Index:
    @login_required
    def GET(self):
        dest = 'adm_ch_tma_bendungan'.split('_')
        redirect_to  = '/adm'
        if session.table_name:
            direct_to = '/adm/' + dest[session.is_admin] + '/' + session.table_name
        elif session.is_admin in (1, 2, 3):
            direct_to = '/adm/' + dest[session.is_admin]
        elif session.is_admin == 9:
            return render.adm.index({})
        return web.seeother(redirect_to, absolute=True)


class Ompong:
    @login_required
    def GET(self):
        skr = datetime.datetime.today()
        if skr.hour > 7:
            dari = skr.replace(hour=7).replace(minute=0).replace(second=0)
        else:
            dari = skr.replace(day=skr.day - 1).replace(hour=7).replace(minute=0).replace(second=0)
        hingga = skr
        arr = [a.table_name for a in Agent.select(Agent.q.AgentType==1.0)]
        sql = "SELECT COUNT(*) FROM %(table_name)s \
            WHERE CONCAT(SamplingDate, ' ', SamplingTime) \
            BETWEEN '%(dari)s' AND '%(hingga)s'"
        rec_count = []
        for a in arr:
            rst = conn.queryAll(sql % {'table_name': a, 'dari': dari, 'hingga': hingga})
            rec_count.append({'table_name': a, 'banyak': rst[0][0]})
        ideal = set([i*5 for i in range(0, 12)])
        return render_anon.cp.ompong({'poses': rec_count})

if __name__ == "__main__":
    #print export_rtow(81)
    print(import_rtow('/tmp/bd_ngancar.csv'))
    #print get_tma_daily_on_pos('jarum', datetime.date(2016, 4, 24))
