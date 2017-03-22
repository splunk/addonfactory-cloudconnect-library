import logging
import os.path as op
import sys
import threading
import time

from cloudconnectlib.client import CloudConnectClient
from cloudconnectlib.common.log import set_cc_logger

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

set_cc_logger(root, '')

context = {
    'snow_host': 'ven01034.service-now.com',
    'table_name': 'incident',
    'sysparm_limit': 100,
    'since_when': '2016-11-01 12:42:23',
    'username': 'splunk',
    'password': 'Splunk123$',
    '__settings__': {
        'logging': {
            'loglevel': 'DEBUG'
        }
    }
}

# test config file
config_file = op.join(op.dirname(op.dirname(__file__)), 'data', 'test_2.json')

if __name__ == '__main__':
    client = CloudConnectClient(context, config_file, None)

    t = threading.Thread(target=client.start)
    t.start()

    time.sleep(100)

    client.stop()
