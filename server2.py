#!/usr/bin/python3
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from sqlalchemy import create_engine
import hashlib
from zeep import Client
import logging
from datetime import datetime
import os
import time

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

# initialize app and API
app = Flask(__name__)
api = Api(app)

# variables definitions
table = 'records'
soapSecretKey = hashlib.md5(b'DasIstEinSehrGeheimesPasswort').hexdigest()

# always ending in "wsdl" (web service description language"
apiEndPoint = "http://ivr-datenimport-123tv.time4quality.de/wsdl.php?WSDL"


class Records(Resource):

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
        date = request.args.get('date', '')
        time = request.args.get('time', '')
        call_id = caller_id + '_' + date + '_' + time

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
            "call_id": call_id
        }

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
