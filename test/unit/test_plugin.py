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
import importlib
import logging
import os
import sys

from . import common

sys.path.append(os.path.join(common.PROJECT_ROOT))
from cloudconnectlib.common import log as ccelog

logger = logging.getLogger("testing")
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s pid=%(process)d tid=%(threadName)s "
    "file=%(filename)s:%(funcName)s:%(lineno)d | %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
ccelog.set_cc_logger(logger)

from cloudconnectlib.core.ext import _extension_functions, lookup_method
from cloudconnectlib.core.plugin import init_pipeline_plugins


def test_decorator():
    from cloudconnectlib.core.plugin import cce_pipeline_plugin

    @cce_pipeline_plugin
    def func_with_arg1(msg):
        return msg

    @cce_pipeline_plugin
    def func_with_arg2(msg, post=""):
        return msg + post

    assert "func_with_arg1" in list(_extension_functions.keys())
    ret = lookup_method("func_with_arg1")("hello")
    assert ret == "hello"

    assert "func_with_arg2" in list(_extension_functions.keys())
    ret = lookup_method("func_with_arg2")("hello")
    assert ret == "hello"

    ret = lookup_method("func_with_arg2")("hello", post="world")
    assert ret == "hello" + "world"

    _extension_functions.pop("func_with_arg1", None)
    _extension_functions.pop("func_with_arg2", None)


def write_py_file(target_dir, target_file, content):
    target_file_path = os.path.join(target_dir, target_file)
    if not os.path.isdir(target_dir):
        os.mkdir(target_dir)

    with open(target_file_path, mode="w") as tf:
        tf.write(content)


def remove_file(target_dir, target_file):
    target_file_path = os.path.join(target_dir, target_file)
    if not os.path.isfile(target_file_path):
        return

    try:
        os.remove(target_file_path)
    except:
        pass


def test_plugin_init_error_path(capsys):
    import_part = """from cloudconnectlib.core.plugin import cce_pipeline_plugin
"""

    test_functions = """
@cce_pipeline_plugin
def cce_unit_test_func_with_arg1(msg):
    return msg

@cce_pipeline_plugin
def cce_unit_test_func_with_arg2(msg, post=""):
    return msg+post

@cce_pipeline_plugin
def json_path(msg):
    return msg

def cce_unit_test_func_without_decorator(msg):
    return msg
"""
    plugin_dir = os.path.join(common.PROJECT_ROOT, "cloudconnectlib", "plugin")
    test_plugin_file1 = "cce_plugin_test_plugin_file1.py"
    test_plugin_file2 = "test_plugin_file2.py"
    test_plugin_file3 = "test_plugin_file3.p"
    test_plugin_file4 = "plugin.py"
    test_plugin_file5 = "cce_plugin_test_plugin_file5.py"
    try:
        # Don't include the decorator or other import error
        _extension_functions.pop("cce_unit_test_func_with_arg1", None)
        _extension_functions.pop("cce_unit_test_func_with_arg2", None)
        write_py_file(plugin_dir, test_plugin_file1, test_functions)
        init_pipeline_plugins(plugin_dir)
        assert "cce_unit_test_func_with_arg1" not in list(_extension_functions.keys())
        assert "cce_unit_test_func_with_arg2" not in list(_extension_functions.keys())

        # Don't have the right prefix
        write_py_file(plugin_dir, test_plugin_file2, import_part + test_functions)
        init_pipeline_plugins(plugin_dir)
        assert "cce_unit_test_func_with_arg1" not in list(_extension_functions.keys())
        assert "cce_unit_test_func_with_arg2" not in list(_extension_functions.keys())

        write_py_file(plugin_dir, test_plugin_file3, import_part + test_functions)
        init_pipeline_plugins(plugin_dir)
        assert "cce_unit_test_func_with_arg1" not in list(_extension_functions.keys())
        assert "cce_unit_test_func_with_arg2" not in list(_extension_functions.keys())

        # The file name already exists
        write_py_file(plugin_dir, test_plugin_file4, import_part + test_functions)
        init_pipeline_plugins(plugin_dir)
        assert "cce_unit_test_func_with_arg1" not in list(_extension_functions.keys())
        assert "cce_unit_test_func_with_arg2" not in list(_extension_functions.keys())

        # The function name already exists
        json_path_value = _extension_functions["json_path"]
        write_py_file(plugin_dir, test_plugin_file5, import_part + test_functions)
        importlib.invalidate_caches()
        init_pipeline_plugins(plugin_dir)
        assert "cce_unit_test_func_with_arg1" in list(_extension_functions.keys())
        assert "cce_unit_test_func_with_arg2" in list(_extension_functions.keys())
        assert _extension_functions["json_path"] == json_path_value

    finally:
        remove_file(plugin_dir, test_plugin_file1)
        remove_file(plugin_dir, test_plugin_file1 + "c")
        remove_file(plugin_dir, test_plugin_file2)
        remove_file(plugin_dir, test_plugin_file2 + "c")
        remove_file(plugin_dir, test_plugin_file3)
        remove_file(plugin_dir, test_plugin_file4)
        remove_file(plugin_dir, test_plugin_file4 + "c")
        remove_file(plugin_dir, test_plugin_file5)
        remove_file(plugin_dir, test_plugin_file5 + "c")


def test_plugin_init(capsys):

    test_functions = """
from cloudconnectlib.core.plugin import cce_pipeline_plugin

@cce_pipeline_plugin
def cce_unit_test_func_with_arg1(msg):
    return msg

@cce_pipeline_plugin
def cce_unit_test_func_with_arg2(msg, post=""):
    return msg+post

def cce_unit_test_func_without_decorator(msg):
    return msg
"""
    plugin_dir = os.path.join(common.PROJECT_ROOT, "cloudconnectlib", "plugin")
    test_plugin_file = "cce_plugin_test_plugin_file.py"
    try:
        _extension_functions.pop("cce_unit_test_func_with_arg1", None)
        _extension_functions.pop("cce_unit_test_func_with_arg2", None)
        write_py_file(plugin_dir, test_plugin_file, test_functions)
        init_pipeline_plugins(plugin_dir)

        assert "cce_unit_test_func_with_arg1" in list(_extension_functions.keys())
        ret = lookup_method("cce_unit_test_func_with_arg1")("hello")
        assert ret == "hello"

        assert "cce_unit_test_func_with_arg2" in list(_extension_functions.keys())
        ret = lookup_method("cce_unit_test_func_with_arg2")("hello", "you")
        assert ret == "hello" + "you"

        assert "cce_unit_test_func_without_decorator" not in list(
            _extension_functions.keys()
        )
    finally:
        remove_file(plugin_dir, test_plugin_file)
        remove_file(plugin_dir, test_plugin_file + "c")


def test_plugin_in_engine_no_files(capsys):
    from cloudconnectlib.core.engine_v2 import CloudConnectEngine

    from .test_engine_v2 import Counter, HTTPJob

    counter = Counter()
    cc_engine = CloudConnectEngine()
    cc_engine.start([HTTPJob(counter)])
    assert counter.value() == 1


def test_plugin_in_engine_w_files(capsys):
    from cloudconnectlib.core.engine_v2 import CloudConnectEngine
    from cloudconnectlib.core.job import CCEJob
    from cloudconnectlib.core.task import CCEHTTPRequestTask

    plugin_dir = os.path.join(common.PROJECT_ROOT, "cloudconnectlib", "plugin")
    test_functions = """
from cloudconnectlib.core.plugin import cce_pipeline_plugin

@cce_pipeline_plugin
def cce_unit_test_func_in_engine_arg1(msg):
    return msg
"""
    error_test_functions = """
from cloudconnectlib.core.plugin import cce_pipeline_plugin

def cce_unit_test_func_in_engine_arg2(msg):
    return msg
"""
    try:
        test_plugin_file1 = "cce_plugin_test_plugin_file1.py"
        write_py_file(plugin_dir, test_plugin_file1, test_functions)
        task = CCEHTTPRequestTask(
            request={
                "url": "https://www.splunk.com/",
                "method": "GET",
            },
            name="test_baidu",
        )

        context = {}
        task.add_postprocess_handler(
            "cce_unit_test_func_in_engine_arg1", ["hello"], "__hello__"
        )
        task.set_iteration_count(1)
        job = CCEJob(context=context)
        job.add_task(task)
        cc_engine = CloudConnectEngine()
        cc_engine.start([job])
        assert context.get("__hello__") == "hello"

        test_plugin_file2 = "cce_plugin_test_plugin_file2.py"
        write_py_file(plugin_dir, test_plugin_file2, error_test_functions)
        task.add_postprocess_handler(
            "cce_unit_test_func_in_engine_arg2", ["world"], "__world__"
        )
        cc_engine.start([job])
        assert context.get("__world__") is None
    finally:
        remove_file(plugin_dir, test_plugin_file1)
        remove_file(plugin_dir, test_plugin_file1 + "c")
        remove_file(plugin_dir, test_plugin_file2)
        remove_file(plugin_dir, test_plugin_file2 + "c")
