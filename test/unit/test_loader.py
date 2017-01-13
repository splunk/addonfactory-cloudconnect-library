import logging
import os.path as op
from os import listdir

import common
import pytest
from cloudconnectlib.common.util import is_valid_port
from cloudconnectlib.common.util import load_json_file
from cloudconnectlib.configuration import get_loader_by_version
from cloudconnectlib.configuration.loader import CloudConnectConfigLoaderV1
from cloudconnectlib.core.exceptions import ConfigException

_config_file = op.join(common.TEST_DATA_DIR, 'test_1.json')


def _schema_file_path_for(schema_file):
    return op.join(common.CONFIGURATION_DIR, schema_file)


def test_load_proxy():
    loader, _ = get_loader_by_version('1.0.0')

    bad_proxy = [{'enabled': 'BAD BOOL',
                  'host': 'host',
                  'port': 'BAD port'},
                 {'enabled': 'BAD BOOL',
                  'host': 'host',
                  'port': '1024'},
                 {'enabled': 'TRUE',
                  'host': 'host',
                  'port': 'BAD port'}
                 ]
    for bp in bad_proxy:
        with pytest.raises(ValueError):
            loader._load_proxy(bp, {})

    good_proxy = [
        {
            'enabled': 'True',
            'host': 'host',
            'port': '1'
        },
        {
            'enabled': 'True',
            'host': 'host',
            'port': '65535'
        },
        {
            'enabled': 'TRUE',
            'host': 'host',
            'port': '1024'
        },
        {
            'enabled': True,
            'host': 'host',
            'port': '1024'
        },
        {
            'enabled': 1,
            'host': 'host',
            'port': '1024'
        },
        {
            'enabled': '1',
            'host': 'host',
            'port': '1024'
        }
    ]

    for gp in good_proxy:
        proxy = loader._load_proxy(gp, {})
        assert proxy['enabled']
        assert proxy['host'] == 'host'
        assert is_valid_port(proxy['port'])

    proxy_with_user = [{'enabled': 'True',
                        'host': 'host',
                        'port': '1',
                        'username': 'admin',
                        'password': 'changeme'},
                       {'enabled': 'True',
                        'host': 'host',
                        'port': '65535',
                        'username': 'admin',
                        'password': 'changeme'},
                       {'enabled': 'TRUE',
                        'host': 'host',
                        'port': '1024',
                        'username': 'admin',
                        'password': 'changeme'}
                       ]
    for pwu in proxy_with_user:
        proxy = loader._load_proxy(pwu, {})
        assert proxy['enabled']
        assert proxy['host'] == 'host'
        assert is_valid_port(proxy['port'])
        assert proxy['username'] == 'admin'
        assert proxy['password'] == 'changeme'


def test_load_global_setting():
    setting_log_only = {
        'logging': {
            'level': 'abc'
        }
    }
    loader, _ = get_loader_by_version('1.0.0')
    setting = loader._load_global_setting(setting_log_only, {})
    assert setting.logging.level == logging.INFO
    setting_log_only['logging']['level'] = 'INFO'
    setting = loader._load_global_setting(setting_log_only, {})

    assert setting.logging.level == logging.INFO
    setting_log_only['logging']['level'] = 'ERROR'
    setting = loader._load_global_setting(setting_log_only, {})
    assert setting.logging.level == logging.ERROR
    assert setting.proxy == {}

    setting_with_proxy = {
        'logging': {
            'level': ' INFO '
        },
        'proxy': {
            'enabled': 'True',
            'host': 'host',
            'port': '1',
            'username': 'admin',
            'password': 'changeme'
        },
    }
    setting = loader._load_global_setting(setting_with_proxy, {})
    assert setting.logging.level == logging.INFO
    assert setting.proxy.enabled
    assert setting.proxy.host == 'host'
    assert setting.proxy.port == '1'
    assert setting.proxy.username == 'admin'
    assert setting.proxy.password == 'changeme'


def test_load_config():
    loader, schema_file = get_loader_by_version('1.0.0')
    conf = load_json_file(_config_file)
    schema_file = _schema_file_path_for(schema_file)

    ctx = {
        '__settings__': {
            'proxy': {
                'proxy_url': 'localhost',
                'proxy_port': '1024',
                'proxy_enabled': '0',
                'proxy_username': 'admin',
                'proxy_password': 'pwd',
                'proxy_type': 'http',
                'proxy_rdns': ''
            }
        }
    }

    config = loader.load(conf, schema_file, ctx)
    assert config.meta.apiVersion == '1.0.0'
    assert config.global_settings.logging.level == logging.INFO
    assert config.global_settings.proxy.enabled is False
    assert config.global_settings.proxy.port == '1024'
    assert config.global_settings.proxy.username == 'admin'
    assert config.global_settings.proxy.password == 'pwd'
    assert config.global_settings.proxy.type == 'http'
    assert config.global_settings.proxy.rdns is False


def test_load_examples():
    files = [f for f in listdir(common.EXAMPLE_DIR) if
             op.isfile(op.join(common.EXAMPLE_DIR, f)) and f.endswith('.json')]

    loader, schema_file = get_loader_by_version('1.0.0')
    schema_file = _schema_file_path_for(schema_file)

    ctx = {
        '__settings__': {
            'proxy': {
                'proxy_url': 'localhost',
                'proxy_port': '1024',
                'proxy_enabled': '0',
                'proxy_username': 'admin',
                'proxy_password': 'pwd',
                'proxy_type': 'http',
                'proxy_rdns': ''
            }
        }
    }

    for f in files:
        loader.load(load_json_file(op.join(common.EXAMPLE_DIR, f)), schema_file, ctx)


def test_get_loader_by_version():
    loader, schema = get_loader_by_version('1.0.0')

    assert schema == 'schema_1_0_0.json'
    assert type(loader) == CloudConnectConfigLoaderV1

    bad_version = ['1.0', '2.0', '3.0', '1.0+']

    for bv in bad_version:
        with pytest.raises(ConfigException):
            get_loader_by_version(bv)
