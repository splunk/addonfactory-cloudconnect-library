#
# Copyright 2021 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
