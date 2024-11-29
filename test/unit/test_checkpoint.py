#
# Copyright 2024 Splunk Inc.
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
import json
import os
import os.path as op

from cloudconnectlib.core.checkpoint import CheckpointManagerAdapter


def test_checkpoint_manager_adapter():
    task_conf = {"appname": "TEST_APPNAME", "stanza_name": "TEST_STANZA_NAME"}
    checkpoint_dir = op.join(op.dirname(op.abspath(__file__)), "checkpoint_dir")
    os.makedirs(checkpoint_dir, exist_ok=True)

    meta_conf = {"checkpoint_dir": checkpoint_dir}
    namespaces = "{{name}}"
    content = {"checkpoint": "{{checkpoint}}"}

    cmgr = CheckpointManagerAdapter(namespaces, content, meta_conf, task_conf)

    cmgr.save({"name": "TEST_NAME", "checkpoint": "CHECKPOINT"})

    filename = op.join(checkpoint_dir, cmgr.get_ckpt_key(["TEST_NAME"])[0])
    with open(filename) as fp:
        assert json.load(fp)["data"] == {"checkpoint": "CHECKPOINT"}

    if op.exists(filename):
        os.remove(filename)
    if op.exists(checkpoint_dir):
        os.removedirs(checkpoint_dir)
