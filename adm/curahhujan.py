'''Admin Curahhujan
'''
import datetime
import web

from helper import to_date, json_serializer
from models import conn, AgentCh, CurahHujan

import paho.mqtt.publish as publish
import json
MQTT_HOST = 'mqtt.bbws-bsolo.net'
MQTT_PORT = 14983
MQTT_TOPIC = 'data_manual'
from helper import to_date, json_serializer


urls = (
    '', 'ChIndex',
    '/update', 'CHUpdate',
    '/terjadi', 'ChTerjadi',
    '/(\w+\.*\-*\w+)', 'ChShow',
    )
    
adm_ch = web.application(urls, locals())
session = web.session.Session(adm_ch, web.session.DiskStore('sessions'),
        initializer={'username': None, 'is_admin': None,
            'table_name': None, 'err': None})


def csrf_token():
    if not session.has_key('csrf_token'):
        from uuid import uuid4
        session['csrf_token'] = uuid4().hex
    return session.get('csrf_token')


globals = {'session': session, 'csrf_token': csrf_token}
render = web.template.render('templates/', base='base_adm', globals=globals)

def pub_object(obj):
    if type(obj) == CurahHujan:
        what = 'ch'
    data = json.dumps(dict(meta={'what': what}, object=obj.sqlmeta.asDict()), default=json_serializer)
    publish.single(MQTT_TOPIC, payload=data, hostname=MQTT_HOST, port=MQTT_PORT)

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


def get_ch_daily_on_pos(pos, today=datetime.date.today()):
    pos = [a for a in AgentCh.select(AgentCh.q.AgentType==1) if a.table_name == pos][0]
    sql = "SELECT id, waktu, manual FROM curahhujan WHERE agent_id=%s AND YEAR(waktu)=%s AND MONTH(waktu)=%s ORDER BY waktu" % (pos.id, today.year, today.month)
    rs = conn.queryAll(sql)
    out = []
    for r in rs:
        out.append(dict(id = r[0], waktu=r[1], ch=r[2]))
    return out


class CHUpdate:
    @login_required
    def POST(self):
        inp = web.input()
        try:
            ch = CurahHujan.get(int(inp.get('pk')))
            ch.set(**{inp.get('name'): float(inp.get('value',0))})
            ch.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}


class ChShow:
    @login_required
    def GET(self, table_name):
        pos = [a for a in AgentCh.select(AgentCh.q.AgentType==1) if a.table_name == table_name][0]
        webinput = web.input(sampling=str(datetime.date.today() - datetime.timedelta(days=1)))
        tg = datetime.datetime.strptime(webinput.sampling, '%Y-%m-%d').date()
        return render.adm.ch.show({'pos': pos, 'tg': tg, 'data': get_ch_daily_on_pos(pos.table_name, tg)})

    @login_required
    def POST(self, table_name):
        try:
            pos = [a for a in AgentCh.select(AgentCh.q.AgentType==1) if a.table_name == table_name][0]
        except IndexError:
            return web.notfound()
        inp = web.input()
        sql = "SELECT id FROM curahhujan WHERE agent_id=%s AND waktu='%s'" % (pos.id, to_date(inp.waktu))
        rs = conn.queryAll(sql)
        if not rs:
            ch = CurahHujan(agent=pos, waktu=to_date(inp.waktu), manual=float(inp.hujan))
            # publish to MQTT Broker
            pub_object(ch)
        return web.redirect('/adm/ch/' + table_name, absolute=True)

class ChTerjadi:
    def GET(self):
        return render.adm.ch.terjadi({})

    def POST(self):
        table_name = 'wonogiri'

        web.header('Content-Type', 'application/vnd.ms-excel')
        web.header('Content-Disposition', 'attachment;filename=' + table_name + '.csv')
        s = '''R1C1,R1C2,R1C3
        R2C1,,R2C3'''
        return s

