"""
    kualitas_air.py
    Aplikasi Kualitas Air

    @author: Widoyo
    @date: 05 Mei 2017
"""
import datetime
import web

from models import Agent, WILAYAH


urls = (
    '$', 'Index',
    '/chart/(\d+)','Chart',
    '/parameter/(\d+)','Parameter',
    '/(\d+)', 'Show',
    '/(\W)', 'ShowByName'
)

app_kualitas_air = web.application(urls, locals())
session = web.session.Session(app_kualitas_air, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'role': None,
                                           'flash': None})

globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)


class Show:
    def GET(self, pid):
        sql = "SELECT k.*, l.id, l.cname, l.ll FROM kualitas_air k, lokasi l WHERE \
                l.id=k.id_pos AND l.id=%d \
                ORDER BY k.waktu" % (int(pid))
        rst = Agent._connection.queryAll(sql)
        if rst:
            pos = (rst[0][-3], rst[0][-2])
            data = [r[:-4] for r in rst]
        return render.kualitas_air.show({'data': data, 'pos': pos})


class ShowByName:
    def GET(self, pos_name):
        pos_name = pos_name.lower()
        return pos_name

class Chart:
    def GET(self,pid):
        conn = Agent._connection
        sql3 = "SELECT YEAR(MAX(waktu)),YEAR(MIN(waktu)) FROM kualitas_air WHERE id_pos= %d" % (int(pid))
        rst3 = conn.queryAll(sql3)
        series_max = int(rst3[0][0])
        series_min = int(rst3[0][1])


        step = (series_max - series_min) + 1
        rows = []
        row_keys = []
        while step!=0:
            sql = "SELECT waktu,ip from kualitas_air WHERE id_pos = %d and YEAR(waktu) = %d" % (int(pid),int(series_max))
            rst = conn.queryAll(sql)
            if rst:
                for d in rst:
                    if d[1] == None:
                        rows.append([int(d[0].strftime('%m'))-1,int(0)])
                    else:
                        rows.append([int(d[0].strftime('%m'))-1,d[1]])
                row_keys.append({'name':str(series_max),'data':rows}) 
                rows=[]
                series_max-=1
                step-=1
            else:
                series_max-=1
                step-=1

        sql2 = "SELECT cname from lokasi where id = %d" % (int(pid))
        rst2 = conn.queryAll(sql2) 
        pos_name = rst2[0][0]

        row_keys.reverse()
        a = str(row_keys)
        row_keys_str = a.replace("'","")

        id_pos_ka = int(pid)
        return render.kualitas_air.chart({'data':row_keys_str,'pname':pos_name,'id_pos_ka':id_pos_ka})

class Parameter:
    def GET(self,pid):
        id_pos_ka = int(pid)
        conn = Agent._connection
        tahun = web.input().get('tahun')
        if not tahun:
            sql = "SELECT waktu,suhu,ph,tds,tss,ot,no3,no2,nh3,po4,cl,fe,mn,na,kok,kob,mbas,cl_2,m_n_l,kmno4,f,s,so4,cn,pb,cu,ni,cr,cr6,b_coli,lab,zn,arsen,fenol,cd,fe_coli FROM kualitas_air WHERE id_pos= %d and YEAR(waktu)=(SELECT MAX(YEAR(waktu)) from kualitas_air where id_pos = %d)" % (int(pid),int(pid))
            rst = conn.queryAll(sql)
        else:
            sql = "SELECT waktu,suhu,ph,tds,tss,ot,no3,no2,nh3,po4,cl,fe,mn,na,kok,kob,mbas,cl_2,m_n_l,kmno4,f,s,so4,cn,pb,cu,ni,cr,cr6,b_coli,lab,zn,arsen,fenol,cd,fe_coli FROM kualitas_air WHERE id_pos= %d and YEAR(waktu)=%d" % (int(pid),int(tahun))
            rst = conn.queryAll(sql)

        waktu = []
        suhu = []
        ph = []
        tds = []
        tss = []
        ot = []
        no3 = []
        no2 = []
        nh3 = []
        po4 = []
        cl = []
        fe = []
        mn = []
        na = []
        kok = []
        kob = []
        mbas = []
        cl_2 = []
        m_n_l = []
        kmno4 = []
        f = []
        s = []
        so4 = []
        cn = []
        pb = []
        cu = []
        ni = []
        cr = []
        cr6 = []
        b_coli = []
        lab = []
        zn = []
        arsen = []
        fenol = []
        cd = []
        fe_coli = []
        for d in rst:
            waktu.append(d[0].strftime('%b %Y'))
            suhu.append(d[1])
            ph.append(d[2])
            tds.append(d[3])
            tss.append(d[4])
            ot.append(d[5])
            no3.append(d[6])
            no2.append(d[7])
            nh3.append(d[8])
            po4.append(d[9])
            cl.append(d[10])
            fe.append(d[11])
            mn.append(d[12])
            na.append(d[13])
            kok.append(d[14])
            kob.append(d[15])
            mbas.append(d[16])
            cl_2.append(d[17])
            m_n_l.append(d[18])
            kmno4.append(d[19])
            f.append(d[20])
            s.append(d[21])
            so4.append(d[22])
            cn.append(d[23])
            pb.append(d[24])
            cu.append(d[25])
            ni.append(d[26])
            cr.append(d[27])
            cr6.append(d[28])
            b_coli.append(d[29])
            lab.append(d[30])
            zn.append(d[31])
            arsen.append(d[32])
            fenol.append(d[33])
            cd.append(d[34])
            fe_coli.append(d[35])

        sql2 = "SELECT cname from lokasi where id = %d" % (int(pid))
        rst2 = conn.queryAll(sql2) 
        pos_name = rst2[0][0]

        sql3 = "select MIN(YEAR(waktu)) as min_year,MAX(YEAR(waktu)) as max_year from kualitas_air where id_pos = %d" %(int(pid))
        rst3 = conn.queryAll(sql3)
        min_year = rst3[0][0]
        max_year = rst3[0][1]
        pilihan_tahun = [a for a in range(min_year,int(max_year)+1,1)]
        #tbl_param = []
        # for d in rst:
        #     tbl_param.append([int(d[0].strftime('%b')),d[1],d[2],d[3]])
        return render.kualitas_air.parameter({'id_pos_ka':id_pos_ka,'waktu':waktu,'suhu':suhu,'ph':ph,'tds':tds,'tss':tss,'ot':ot,'no3':no3,'no2':no2,'nh3':nh3,'po4':po4,'cl':cl,'fe':fe,'mn':mn,'na':na,'kok':kok,'kob':kob,'mbas':mbas,'cl_2':cl_2,'m_n_l':m_n_l,'kmno4':kmno4,'f':f,'s':s,'so4':so4,'cn':cn,'pb':pb,'cu':cu,'ni':ni,'cr':cr,'cr6':cr6,'b_coli':b_coli,'lab':lab,'zn':zn,'arsen':arsen,'fenol':fenol,'cd':cd,'fe_coli':fe_coli,'pos_name':pos_name,'pilihan_tahun':pilihan_tahun})

    def POST(self,tahun):
        tahun = int(tahun)
        return "anda memilih tahun "+tahun

class Index:
    def GET(self):
        tahun = ''
        conn = Agent._connection
        sql = "SELECT YEAR(MAX(waktu)) FROM kualitas_air"
        rst = conn.queryAll(sql)
        if not rst:
            return "Tidak ada data Kualitas Air"
        # sql = "SELECT k.waktu, k.ip, l.id, l.cname, l.ll \
        #         FROM kualitas_air k, lokasi l \
        #         WHERE k.id_pos=l.id AND YEAR(k.waktu)=%s \
        #         ORDER BY l.id, k.waktu" % rst[0][0]
        sql = "SELECT MAX(k.waktu), k.ip, l.id, l.cname, l.ll, l.wilayah, l.urutan \
                FROM kualitas_air k, lokasi l \
                WHERE k.id_pos=l.id GROUP BY l.id ORDER BY l.wilayah, l.urutan ASC"
        rst = conn.queryAll(sql)
        rows = []
        waktu = datetime.date.today()
        for d in rst:
            #kode untuk menyembunyikan pos tertentu di tabel kualitas air
            if d[3] == "Embanmati" or d[3] == "Grompol":
                continue
            rows.append((d[2], d[3], d[0].strftime('%b %Y'), d[0].strftime('%Y'), d[5]))

        return render.kualitas_air.index({'data': rows,'wilayah':WILAYAH})
