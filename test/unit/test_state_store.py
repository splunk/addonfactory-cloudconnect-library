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
import os
import os.path as op
from contextlib import contextmanager

from splunktalib import state_store


@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


def _clean_up(checkpoint_dir, filename):
    with ignored(OSError):
        os.remove(op.join(checkpoint_dir, filename))
    with ignored(OSError):
        os.rmdir(checkpoint_dir)


def test_update_file_state_store():
    checkpoint_dir = op.join(op.dirname(__file__), "test_checkpoint_dir")
    os.makedirs(checkpoint_dir, exist_ok=True)
    filename = "checkpoint_file_for_update"
    if not os.path.exists(op.join(checkpoint_dir, filename)):
        open(op.join(checkpoint_dir, filename + ".new"), "w+")

    _clean_up(checkpoint_dir, filename)

    fss = state_store.FileStateStore(
        appname="TestApp", meta_configs={"checkpoint_dir": checkpoint_dir}
    )

    checkpoint = fss.get_state(filename)
    assert checkpoint is None
    checkpoint = {"a1": "str", "a2": 124, "a3": [1, 2, 3]}
    fss.update_state(filename, checkpoint)
    checkpoint = fss.get_state(filename)

    assert checkpoint is not None
    assert checkpoint["a1"] == "str"
    assert checkpoint["a2"] == 124
    assert checkpoint["a3"] == [1, 2, 3]

    _clean_up(checkpoint_dir, filename)


def test_delete_file_state_store():
    checkpoint_dir = op.join(op.dirname(__file__), "test_checkpoint_dir2")
    os.makedirs(checkpoint_dir, exist_ok=True)
    filename = "checkpoint_file_for_delete"
    if not os.path.exists(op.join(checkpoint_dir, filename)):
        open(op.join(checkpoint_dir, filename + ".new"), "w+")

    _clean_up(checkpoint_dir, filename)

    fss = state_store.FileStateStore(
        appname="TestApp", meta_configs={"checkpoint_dir": checkpoint_dir}
    )
    checkpoint = {"a1": "str", "a2": 124, "a3": [1, 2, 3]}
    fss.update_state(filename, checkpoint)
    checkpoint = fss.get_state(filename)

    assert checkpoint is not None
    assert checkpoint["a1"] == "str"
    assert checkpoint["a2"] == 124
    assert checkpoint["a3"] == [1, 2, 3]

    fss.delete_state(filename)

    checkpoint = fss.get_state(filename)
    assert checkpoint is None

    _clean_up(checkpoint_dir, filename)
