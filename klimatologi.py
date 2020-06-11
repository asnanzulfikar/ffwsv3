"""
    klimatologi.py
    Aplikasi Klimatologi

    @author: Widoyo
    @date: 12 Aug 2017
"""
import datetime
import web
from sqlobject import func

from common_data import KLIMATOLOGI_POS
from models import Agent, KlimatManual
from helper import to_date

urls = (
    '$', 'Index',
)


app_klimatologi = web.application(urls, locals())
session = web.session.Session(app_klimatologi, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'role': None,
                                           'flash': None})

globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)


class Index:
    def GET(self):
        try:
            tanggal = to_date(web.input().get('d'))
        except:
            tanggal = datetime.date.today() - datetime.timedelta(days=1)
        poses = dict([l.split('\t') for l in open(
            'agent_table.txt').readlines()])
        klimat_manual = KlimatManual.select(func.DATE(KlimatManual.q.sampling) == tanggal)

        return render.klimatologi.index({'pos': klimat_manual, 'tanggal': tanggal, 'sebelum': tanggal - datetime.timedelta(days=1), 'sesudah': tanggal + datetime.timedelta(days=1)})


def test_segmented_klimatologi():
    tgl = datetime.date(2017, 9, 23)
    pabelan = Agent.get(9)
    jurug = Agent.get(2)
    print('Pabelan', pabelan.get_segmented_klimatologi(tgl))
    print('Jurug', jurug.get_segmented_klimatologi(tgl))



if __name__ == '__main__':
    test_segmented_klimatologi()
