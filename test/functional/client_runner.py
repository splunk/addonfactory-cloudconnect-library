import os.path as op
import threading
import time

from cloudconnectlib.client import CloudConnectClient

context = {
    'host': 'ven01034.service-now.com',
    'table_name': 'incident',
    'sysparm_limit': 100,
    'since_when': '2016-11-01 12:42:23',
    'username': 'splunk',
    'password': 'Splunk123$',
}

# test config file
config_file = op.join(op.dirname(op.dirname(__file__)), 'data', 'test_2.json')

if __name__ == '__main__':
    client = CloudConnectClient(context, config_file, None)

    t = threading.Thread(target=client.start)
    t.start()

    time.sleep(10)

    client.stop()
