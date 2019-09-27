from __future__ import absolute_import
import os.path as op

import pytest
from cloudconnectlib.client import CloudConnectClient
from cloudconnectlib.core.engine import CloudConnectEngine
from cloudconnectlib.core.exceptions import ConfigException
from .common import TEST_DATA_DIR


def test_client(monkeypatch):
    engine_status = [0]

    def mock_engine_start(self, context, config, checkpoint_mgr):
        engine_status[0] = 'started'

    def mock_engine_stop(self):
        engine_status[0] = 'stopped'

    monkeypatch.setattr(CloudConnectEngine, 'start', mock_engine_start)
    monkeypatch.setattr(CloudConnectEngine, 'stop', mock_engine_stop)

    context = {
        'host': 'ven01034.service-now.com',
        'table_name': 'incident',
        'sysparm_limit': 100,
        'since_when': '2016-11-01 12:42:23',
        'username': 'splunk',
        'password': 'Splunk123$',
        '__settings__': {
            'logging': {},
            'proxy': {
                'proxy_enabled': False
            }
        }
    }
    filepath = op.join(TEST_DATA_DIR, 'file_not_exist.json')
    client = CloudConnectClient(context, filepath, None)

    with pytest.raises(ConfigException):
        client.start()

    filepath = op.join(TEST_DATA_DIR, 'test_4.json')
    client = CloudConnectClient(context, filepath, None)

    client.start()
    assert engine_status[0] == 'started'

    client.stop()
    assert engine_status[0] == 'stopped'
