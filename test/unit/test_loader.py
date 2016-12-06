import logging
import os.path as op

import pytest

from package.cloudconnectlib.configuration import CloudConnectConfigLoaderV1
from package.cloudconnectlib.core import ConfigException
from package.cloudconnectlib.core.util import is_port

_config_file = op.join(op.dirname(op.dirname(op.abspath(__file__))), 'data', 'test_1.json')


def test_load_proxy():
    loader = CloudConnectConfigLoaderV1()

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
        with pytest.raises(ConfigException):
            loader._load_proxy(bp, {})

    good_proxy = [{'enabled': 'True',
                   'host': 'host',
                   'port': '1'},
                  {'enabled': 'True',
                   'host': 'host',
                   'port': '65535'},
                  {'enabled': 'TRUE',
                   'host': 'host',
                   'port': '1024'}
                  ]

    for gp in good_proxy:
        proxy = loader._load_proxy(gp, {})
        assert proxy['enabled']
        assert proxy['host'] == 'host'
        assert is_port(proxy['port'])

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
        assert is_port(proxy['port'])
        assert proxy['username'] == 'admin'
        assert proxy['password'] == 'changeme'


def test_load_global_setting():
    setting_log_only = {
        'logging': {
            'level': 'abc'
        }
    }
    loader = CloudConnectConfigLoaderV1()
    setting = loader._load_global_setting(setting_log_only, {})
    import logging
    assert setting.logging.level == logging.INFO
    setting_log_only['logging']['level'] = 'INFO'
    setting = loader._load_global_setting(setting_log_only, {})

    assert setting.logging.level == logging.INFO
    setting_log_only['logging']['level'] = 'ERROR'
    setting = loader._load_global_setting(setting_log_only, {})
    assert setting.logging.level == logging.ERROR
    assert setting.proxy is None

    setting_with_proxy = {
        'logging': {
            'level': 'INFO'
        },
        'proxy': {'enabled': 'True',
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
    loader = CloudConnectConfigLoaderV1()
    config = loader.load_config(_config_file, {
        'proxy_port': '1024',
        'proxy_enabled': '0',
        'proxy_username': 'admin',
        'proxy_password': 'pwd',
        'proxy_type': 'http',
        'proxy_rdns': ''
    })
    assert config.meta.version == '1.0.0'
    assert config.global_settings.logging.level == logging.INFO
    assert config.global_settings.proxy.enabled is False
    assert config.global_settings.proxy.port == '1024'
    assert config.global_settings.proxy.username == 'admin'
    assert config.global_settings.proxy.password == 'pwd'
    assert config.global_settings.proxy.type == 'http'
    assert config.global_settings.proxy.rdns is False
