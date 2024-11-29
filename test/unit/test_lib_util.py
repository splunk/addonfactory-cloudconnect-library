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
import sys

from cloudconnectlib.common.lib_util import register_module


def test_register_module():
    module_not_exist = "cloudconnect_test"

    system_path = sys.path
    assert module_not_exist not in system_path

    register_module(module_not_exist)
    assert module_not_exist not in system_path

    import os.path as op

    module_exist = op.abspath(__file__)
    register_module(module_exist)

    assert module_exist in system_path
    assert system_path[0] == module_exist

    del system_path[0]
