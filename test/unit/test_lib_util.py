import sys

from cloudconnectlib.common.lib_util import register_module


def test_register_module():
    module_not_exist = 'cloudconnect_test'

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
