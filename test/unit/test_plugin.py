import pytest
import sys
import os
import common
sys.path.append(os.path.join(common.PROJECT_ROOT, "package"))

import cloudconnectlib
from cloudconnectlib.core.plugin import cce_pipeline_plugin
from cloudconnectlib.core.ext import _extension_functions


@cce_pipeline_plugin
def func_with_arg1(msg):
    return msg


@cce_pipeline_plugin
def func_with_arg2(msg, post=""):
    return msg+post


def test_decorator():
    assert "func_with_arg1" in _extension_functions.keys()
    ret = func_with_arg1("hello")
    assert ret == "hello"

    assert "func_with_arg2" in _extension_functions.keys()
    ret = func_with_arg2("hello")
    assert ret == "hello"

    ret = func_with_arg2("hello", post="world")
    assert ret == "hello"+"world"
