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

now = datetime.now()
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

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

SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://ciox:Ciox123@sqlazure:1433/restApi?driver=SQL+Server+Native+Client+11.0'

# initialize app and API
db_connect = create_engine(SQLALCHEMY_DATABASE_URI)
app = Flask(__name__)
api = Api(app)

# variables definitions
table = 'records'
soapSecretKey = hashlib.md5(b'DasIstEinSehrGeheimesPasswort').hexdigest()

# always ending in "wsdl" (web service description language"
apiEndPoint = "http://ivr-datenimport-123tv.time4quality.de/wsdl.php?WSDL"

class Records(Resource):

#    def get(self):
#        conn = db_connect.connect() # connect to database
#        query = conn.execute("select * from {0}".format(table)) # This line performs query and returns json result
#        return {'data': [dict(zip(tuple (query.keys()), i)) for i in query.cursor]}

    def get(self):
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

        # get data from POST request from Avaya
        line = 'CC2Servicenummer'
        standort = 'Belgrad'
        prozess = 'Nicht übermittelt'
        agent = request.args.get('agent', '')
        caller_id = request.args.get('caller_id', '')
        geschaeftsvorfall = ''
        kundennummer = 'Nicht übermittelt'
        call_id = '32ggr3bfgf'

        # dictionary to send via SOAP
        data = {
            "auth": soapSecretKey,
            "line": "CC2Servicenummer",
            "standort": "Belgrad",
            "prozess": "Nicht übermittelt",
            "agent": agent,
            "caller_id": caller_id,
            "geschaeftsvorfall": "",
            "kundennummer": "Nicht übermittelt",
            "call_id": "32ggr3bfgf"
        }

        # connect to the database
        try:
            logger.info('Connect to DB')
            conn = db_connect.connect()
        except Exception as e:
            logger.info('Failed on TRIZMA DB connect at: '
                        + str(timestamp)
                        + ', for following calling party: '
                        + str(caller_id)
                        + ', for agent id: '
                        + str(agent)
                        + ', with error:'
                        + str(e))

        # query execution (load data to Trizma's database)
        try:
            logger.info('TRIZMA DB import')
            query = conn.execute("insert into {0} values('{1}','{2}','{3}','{4}', \
                                 '{5}','{6}','{7}','{8}')".format(table,line,standort,prozess,
                                 agent, caller_id, geschaeftsvorfall, kundennummer,call_id))
        except Exception as e:
            logger.info('Failed on TRIZMA DB import at: '
                        + str(timestamp)
                        + ', for following calling party: '
                        + str(caller_id)
                        + ', for agent id: '
                        + str(agent)
                        + ', with error:'
                        + str(e))

        # soap client initialization
        try:
            logger.info('123TV DB import')
            soap_client = Client(apiEndPoint)
            soap_client.service.importCallMetaData(**data)

            return {'status': 'success'}
        except Exception as e:
            logger.info('Failed on 123TV DB import at: '
                        + str(timestamp)
                        + ', for following calling party: '
                        + str(caller_id)
                        + ', for agent id: '
                        + str(agent)
                        + ', with error:'
                        + str(e))

api.add_resource(Records, '/records') # Route_1
# api.add_resource(Tracks, '/tracks') # Route_2
# api.add_resource(Employees_Name, '/employees/<employee_id>') # Route_3

if __name__ == '__main__':
     app.run()