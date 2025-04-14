#
# Copyright 2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os.path as op

import pytest

from cloudconnectlib.client import CloudConnectClient
from cloudconnectlib.core.engine import CloudConnectEngine
from cloudconnectlib.core.exceptions import ConfigException

from .common import TEST_DATA_DIR


def test_client(monkeypatch):
    engine_status = [0]

    def mock_engine_start(self, context, config, checkpoint_mgr):
        engine_status[0] = "started"

    def mock_engine_stop(self):
        engine_status[0] = "stopped"

    monkeypatch.setattr(CloudConnectEngine, "start", mock_engine_start)
    monkeypatch.setattr(CloudConnectEngine, "stop", mock_engine_stop)

    context = {
        "host": "ven01034.service-now.com",
        "table_name": "incident",
        "sysparm_limit": 100,
        "since_when": "2016-11-01 12:42:23",
        "username": "splunk",
        "password": "Splunk123$",
        "__settings__": {"logging": {}, "proxy": {"proxy_enabled": False}},
    }
    filepath = op.join(TEST_DATA_DIR, "file_not_exist.json")
    client = CloudConnectClient(context, filepath, None)

    with pytest.raises(ConfigException):
        client.start()

    filepath = op.join(TEST_DATA_DIR, "test_4.json")
    client = CloudConnectClient(context, filepath, None)

    client.start()
    assert engine_status[0] == "started"

    client.stop()
    assert engine_status[0] == "stopped"
