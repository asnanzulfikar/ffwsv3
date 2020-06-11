import datetime

from models import Agent, WadukDaily, conn

lines = open('/tmp/pow.txt').readlines()

th = 2017

dict_agent = dict([(a.table_name, a.AgentId) for a in Agent.select(Agent.q.AgentType==3)])

#f = open('/tmp/out.txt', 'w')
for l in lines:
    (n, d, data) = l.strip().split('\t', 2)
    # print n
    b = 11
    waktu = datetime.date(th, b, 1)
    pows = data.strip().split('\t')
    for i in range(len(pows)):
        if not i % 2:
            while waktu.day <= 15:
                sql = "SELECT id FROM waduk_daily WHERE pos_id=%s AND waktu='%s'" % (dict_agent[n], waktu)
                rst = conn.queryAll(sql)
                if rst:
                    wd = WadukDaily.get(rst[0][0])
                    print wd.waktu, n
                    wd.po_outflow_q = float(pows[i])
                    #print rst
                else:
                    wd = WadukDaily(**dict(pos=dict_agent[n], waktu=waktu, po_outflow_q=float(pows[i])))
                    print n, waktu
                #print dict_agent[n], n, waktu, pows[i]
                waktu += datetime.timedelta(days=1)
        else:
            while waktu.day != 1:
                sql = "SELECT id FROM waduk_daily WHERE pos_id=%s AND waktu='%s'" % (dict_agent[n], waktu)
                rst = conn.queryAll(sql)
                if rst:
                    wd = WadukDaily.get(rst[0][0])
                    print wd.waktu, n
                    wd.po_outflow_q = float(pows[i])
                else:
                    wd = WadukDaily(**dict(pos=dict_agent[n], waktu=waktu, po_outflow_q=float(pows[i])))
                    print n, waktu
                    #print rst
                #print dict_agent[n], n, waktu, pows[i]
                waktu += datetime.timedelta(days=1)
