
from sqlobject import SQLObject, connectionForURI, sqlhub
from sqlobject import StringCol, IntCol

cs = "mysql://root@localhost/telemetri"
con4 = connectionForURI(cs)
sqlhub.processConnection = con4

ARR = 1
AWLR = 2
BENDUNGAN = 3


class Pos(SQLObject):
    nama = StringCol(length=50, unique=True)
    ll = StringCol(length=50)
    tipe = IntCol()
