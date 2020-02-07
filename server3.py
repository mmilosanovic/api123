#!/usr/bin/python3
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from sqlalchemy import create_engine
import hashlib
from zeep import Client
import logging
from datetime import datetime
import os
from json import dumps

timestamp = datetime.now().strftime("%Y-%m-%d")

# create logs folder if it does not exist
# logFileFolder = 'C:/Users/mmilosanovic/Desktop/logs'
logFileFolder = '/home/python_project/logs'

if not os.path.exists(logFileFolder):
    os.makedirs(logFileFolder)

logFilePath = os.path.join(logFileFolder,
                           'logFile_' + timestamp + '.log')

logger = logging.getLogger(__name__)
logConfig = logging.basicConfig(level=logging.INFO,
                                format='%(asctime)s - %(levelname)s - %(message)s',
                                datefmt='%a, %d %b %Y %H:%M:%S',
                                filename=logFilePath,
                                filemode='w')

SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://ciox:Ciox123@13.79.224.241:1433/restApi?driver=ODBC+Driver+17+for+SQL+Server'

# initialize app and API
db_connect = create_engine(SQLALCHEMY_DATABASE_URI)
app = Flask(__name__)
api = Api(app)

# variables definitions
table = 'records'
tableDimAgents = 'dimAgents'
soapSecretKey = hashlib.md5(b'DasIstEinSehrGeheimesPasswort').hexdigest()

# always ending in "wsdl" (web service description language"
apiEndPoint = "http://ivr-datenimport-123tv.time4quality.de/wsdl.php?WSDL"


@app.route('/')
def hello_world():
    return 'Trizma RESTful API'


class Records(Resource):

    # def get(self):
    #     conn = db_connect.connect() # connect to database
    #     query = conn.execute("select * from {0}".format(table)) # This line performs query and returns json result
    #     return {'data': [dict(zip(tuple (query.keys()), i)) for i in query.cursor]}

    def get(self):
        timestampGet = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # get data from GET request from Avaya
        line = 'CC2Servicenummer'
        standort = 'Belgrad'
        prozess = 'Nicht übermittelt'
        agent = request.args.get('agent', '')
        caller_id = request.args.get('caller_id', '')
        geschaeftsvorfall = ''
        kundennummer = 'Nicht übermittelt'
        date = request.args.get('date', '')
        time = request.args.get('time', '')
        call_id = caller_id + '_' + date + '_' + time

        if caller_id == None:
            caller_id == 'CALLER_ID NOT SENT VIA GET.'
            logger.info('Connect to DB:::: CALLER_ID NOT SENT VIA GET.')
        
        tries = 5
        for i in range(tries):
            try:
                logger.info('Connect to DB:::: Try #' + str(i+1) + ' START.')
                conn = db_connect.connect()
                
                agentUsername = conn.execute(
                    "select qmUser from {0} where cmsID = {1} and active = {2}".format(tableDimAgents,
                                                                                       int(agent),
                                                                                       1)).fetchone()[0]

                filenameAgentUsername = conn.execute(
                    "select filenameUser from {0} where cmsID = {1} and active = {2}".format(tableDimAgents,
                                                                                             int(agent),
                                                                                             1)).fetchone()[0]
                logger.info('Connect to DB:::: Try #' + str(i+1) + ' SUCCESS.')
                
            except Exception as e:
                
                if i < tries - 1: # i is zero indexed
                    logger.info('Connect to DB:::: Fail #' + str(i+1) + ': ' + str(e))
                    sleep(3)
                    continue
                else:
                    agentUsername = 'agentUsername not fetched from TRIZMA DB.'
                    filenameAgentUsername = 'filenameAgentUsername not fetched from TRIZMA DB.'
                    logger.info('Failed on TRIZMA DB connect at:::: '
                            + str(timestampGet)
                            + ', for following calling party: '
                            + str(caller_id)
                            + ', for agent id: '
                            + str(agentUsername)
                            + ', with error:'
                            + str(e))
            break

        # dictionary to send via SOAP
        data = {
            "auth": soapSecretKey,
            "line": "CC2Servicenummer",
            "standort": "Belgrad",
            "prozess": "Nicht übermittelt",
            "agent": agentUsername,
            "caller_id": caller_id,
            "geschaeftsvorfall": "",
            "kundennummer": "Nicht übermittelt",
            "call_id": call_id,
            "acd_id": filenameAgentUsername,
        }

        # query execution (load data to Trizma's database)
        try:
            logger.info('TRIZMA DB import:::: START')
            query = conn.execute("insert into {0} values('{1}','{2}','{3}','{4}', \
                                '{5}','{6}','{7}','{8}','{9}',{10})".format(table, line, standort, prozess,
                                                                       agentUsername, caller_id, geschaeftsvorfall,
                                                                       kundennummer, call_id, filenameAgentUsername, timestampGet))
            logger.info('TRIZMA DB import:::: SUCCESS')
        except Exception as e:
            logger.info('Failed on TRIZMA DB import at:::: '
                        + str(timestampGet)
                        + ', for following calling party: '
                        + str(caller_id)
                        + ', for agent id: '
                        + str(agentUsername)
                        + ', with error:'
                        + str(e))

        if agentUsername != 'agentUsername not fetched from TRIZMA DB.' and filenameAgentUsername != 'filenameAgentUsername not fetched from TRIZMA DB.':
            # soap client initialization
            try:
                logger.info('123TV DB import:::: START')
                soap_client = Client(apiEndPoint)
                soap_client.service.importCallMetaData(**data)
                logger.info('123TV DB import:::: SUCCESS')
                
                return {'status': 'success'}
            except Exception as e:
                logger.info('Failed on 123TV SOAP import at:::: '
                            + str(timestampGet)
                            + ', for following calling party: '
                            + str(caller_id)
                            + ', for agent id: '
                            + str(agent)
                            + ', with error:'
                            + str(e) + data)
        else:
            logger.info('123TV DB import:::: agentUsername or filenameAgentUsername not fetched from TRIZMA DB.')


api.add_resource(Records, '/records')  # Route_1
# api.add_resource(Tracks, '/tracks') # Route_2
# api.add_resource(Employees_Name, '/employees/<employee_id>') # Route_3

if __name__ == '__main__':
    app.run()
