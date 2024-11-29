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
import pytest

from cloudconnectlib.core.exceptions import CCESplitError
from cloudconnectlib.core.task import CCESplitTask

context = {"apps": ["app1", "app2", "app3"]}


def test_split_task_for_list():
    splittask = CCESplitTask("test_split_task_for_list")
    context = {"apps": ["app1", "app2", "app3"]}
    splittask.configure_split("split_by", "{{apps}}", "app")
    results = splittask.perform(context)
    results = list(results)
    assert len(results) == 3
    assert results[0]["app"] is not None


def test_split_task_for_empty_list():
    splittask = CCESplitTask("test_split_task_for_list")
    context = {"apps": []}
    splittask.configure_split("split_by", "{{apps}}", "app")
    results = splittask.perform(context)
    with pytest.raises(CCESplitError):
        results = list(results)

    context = {"apps_2": ["app1", "app2", "app3"]}
    results = splittask.perform(context)
    with pytest.raises(CCESplitError):
        results = list(results)


def test_split_task_for_string():
    splittask = CCESplitTask("test_split_task_for_list")
    splittask.configure_split("split_by", "{{apps}}", "app", ",")
    context = {"apps": "app1, app2, app3"}
    results = splittask.perform(context)
    results = list(results)
    assert len(results) == 3
    assert results[0]["app"] is not None

    context = {"apps": "app1"}
    results = splittask.perform(context)
    results = list(results)
    assert len(results) == 1
    assert results[0]["app"] is not None


def test_split_task_for_empty_string():
    splittask = CCESplitTask("test_split_task_for_list")
    splittask.configure_split("split_by", "{{apps}}", "app", ",")
    context = {"apps": ""}
    results = splittask.perform(context)
    with pytest.raises(CCESplitError):
        results = list(results)
