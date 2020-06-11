import cPickle
from models import Agent, conn

def upload():
    to_load = {}
    with open('/tmp/svrdata.pkl', 'rb') as f:
        to_load = cPickle.load(f)
    for d in to_load.get('pos_to_put', []):
        try:
            agent = Agent.select(Agent.q.AgentName == d['name'])[0]
        except IndexError:
            try:
                agent = Agent(**d['data'])
                # karena 'id'nya tidak standar,
                # SQLObject bilang Not Found
            except SQLObjectNotFound:
                agent = Agent.select(Agent.q.AgentName == d['name'])[0]

        # Periksa apakah table pemuat Logs untuk
        # pos ini telah tersedia
        try:
            rs = conn.queryAll("SELECT SamplingDate FROM %s \
                LIMIT 0, 1" % (agent.table_name))
        except:
            rs = conn.queryAll("CREATE TABLE %s \
                LIKE tpl_agent" % agent.table_name)
        print agent.AgentName
        for l in d['logs']:
            print '\t', l['SamplingDate'], l['SamplingTime']
            sql = "SELECT COUNT(*) FROM %s \
               WHERE SamplingDate='%s' AND \
               SamplingTime='%s'" % (agent.table_name,
                l['SamplingDate'],
                l['SamplingTime'])
            rs = conn.queryAll(sql)
            print '\t\trs[0][0]:', rs[0][0]
            if rs[0][0] == 0:

                sql = "INSERT INTO %s (RID, ReceivedDate, \
                    ReceivedTime, DataType, StatusPort, \
                   SamplingDate, SamplingTime, Temperature, \
                   Humidity, Rain, Rain1, Rain2, Rain3, \
                   Rain4, WLevel, Wlevel1, WLevel2, \
                    WLevel3, WLevel4, up_since, sq) VALUES (%s, '%s', \
                    '%s', %s, '%s', '%s', '%s', %s, %s, \
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, \
                    %s, '%s', %s)" % (agent.table_name, l['RID'],
                        l['ReceivedDate'],
                        l['ReceivedTime'],
                            l['DataType'],
                            l['StatusPort'],
                            l['SamplingDate'],
                            l['SamplingTime'],
                            l['Temperature'],
                            l['Humidity'],
                            l['Rain'],
                            l['Rain1'],
                            l['Rain2'],
                            l['Rain3'],
                            l['Rain4'],
                            l['WLevel'],
                            l['WLevel1'],
                            l['WLevel2'],
                            l['WLevel3'],
                            l['WLevel4'],
                            l['up_since'],
                            l['sq']) 
                rs = conn.query(sql)
                print '\tsaved:', l['SamplingDate'], l['SamplingTime']
                del l



if __name__ == '__main__':
    upload()
