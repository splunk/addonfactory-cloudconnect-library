import json
import os.path as op

from jsonschema import validate

from package.cloudconnectlib.core.model.config import CloudConnectConfig
from . import util
from .model import (
    Meta, Proxy, Logging, GlobalSetting, Request, Header, Condition,
    Options, Checkpoint, BeforeRequest, AfterRequest, SkipAfterRequest
)

# JSON schema file path.
_SCHEMA_LOCATION = op.join(op.dirname(op.dirname(__file__)), 'configuration',
                           'hcm_schema.json')

_PROXY_TYPES = ['http', 'socks4', 'socks5', 'http_no_tunnel']


def _json_file(file_path):
    with open(file_path, 'r') as r:
        return json.load(r)


def _load_schema_from_file(file_path):
    """
    Load JSON based schema definition from file.
    :param file_path: JSON based schema file path.
    :return: A `dict` contains schema.
    """
    try:
        return _json_file(file_path)
    except:
        raise ValueError('Cannot load schema from {}'.format(file_path))


def _load_definition(file_path):
    """
    Load user's JSON interface definition from file.
    :param file_path: JSON interface file path.
    :return: A `dict` contains user defined JSON interface.
    """
    if not op.isfile(file_path):
        raise ValueError('Invalid interface file {}'.format(file_path))
    try:
        return _json_file(file_path)
    except:
        raise ValueError('Cannot load JSON interface from file {}'.format(file_path))


class _BaseLoader(object):
    @classmethod
    def load(cls, config):
        pass


def _ensure_list(obj, msg):
    assert isinstance(obj, list), msg


def _ensure_dict(obj, msg):
    assert isinstance(obj, dict), msg


def _check_required_fields(fields, config):
    for f in fields:
        if f not in config:
            raise ValueError('Field {} is required'.format(f))


class MetaLoader(_BaseLoader):
    _required_fields = ['version']

    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'Meta expect to be a dict')
        _check_required_fields(cls._required_fields, config)
        return Meta(config)


class ProxyLoader(_BaseLoader):
    _required_fields = ['enabled', 'host', 'port']

    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'Proxy expect to be a dict')
        _check_required_fields(cls._required_fields, config)

        enabled = config['enabled']
        if not util.is_bool(enabled):
            raise ValueError('Proxy "enabled" expect to be a bool')
        port = config['port']
        if not util.is_port(port):
            raise ValueError('Invalid proxy port: {}'.format(port))

        # proxy type default to `http`
        proxy_type = config.get('type')
        if proxy_type and proxy_type not in _PROXY_TYPES:
            raise ValueError('Invalid proxy type: {}'.format(proxy_type))

        return Proxy(enabled=enabled, host=config['host'], port=port,
                     type=proxy_type, rdns=config.get('rdns'))


class LoggingLoader(_BaseLoader):
    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'Logging expect to be a dict')
        return Logging(level=config.get('level'))


class GlobalSettingLoader(_BaseLoader):
    @classmethod
    def load(cls, config):
        if config is None:
            return None
        _ensure_dict(config, 'GlobalSetting expect to be a dict')
        proxy = ProxyLoader.load(config['proxy']) if 'proxy' in config else None
        logging = LoggingLoader.load(config['logging']) if 'logging' in config else None
        return GlobalSetting(proxy=proxy, logging=logging)


class HeaderLoader(_BaseLoader):
    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'Header expect to be a dict')
        header = Header()
        for k, v in config:
            header.add(k, v)
        return header


class OptionsLoader(_BaseLoader):
    _required_fields = ['url', 'method', 'headers']

    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'Options expect to be a dict')
        _check_required_fields(cls._required_fields, config)

        header = HeaderLoader.load(config['header'])
        method = config['method']
        url = config['url']
        return Options(header=header, method=method, url=url,
                       auth=config.get('auth'))


class CheckpointLoader(_BaseLoader):
    _required_fields = ['namespace', 'content']

    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'Checkpoint expect to be a dict')
        _check_required_fields(cls._required_fields, config)
        namespace = config['namespace']
        _ensure_list(namespace, 'Namespace expect to be a list')
        content = config['content']
        _ensure_dict(content, 'Content expect to be a dict')
        return Checkpoint(namespace, content)


class BeforeRequestLoader(_BaseLoader):
    _required_fields = ['input', 'method']

    @classmethod
    def load(cls, config):
        _ensure_list(config, 'BeforeRequests expect to be a list')
        elements = []
        for item in config:
            _ensure_dict(item, 'BeforeRequest in  expect to be a list')
            _check_required_fields(cls._required_fields, item)
            _ensure_list(item['input'], 'Input expect to be a list')
            elements.append(BeforeRequest(item['input'], item['method'],
                                          item.get('output')))
        return elements


class AfterRequestLoader(_BaseLoader):
    _required_fields = ['input', 'method']

    @classmethod
    def load(cls, config):
        _ensure_list(config, 'AfterRequests expect to be a list')
        elements = []
        for item in config:
            _ensure_dict(item, 'AfterRequest expect to be a list')
            _check_required_fields(cls._required_fields, item)
            _ensure_list(item['input'], 'Input expect to be a list')
            elements.append(AfterRequest(item['input'], item['method'],
                                         item.get('output')))
        return elements


class ConditionLoader(_BaseLoader):
    _required_fields = ['input', 'method']

    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'Condition expect to be a dict')
        _check_required_fields(cls._required_fields, config)
        inputs = config['input']
        _ensure_list(inputs, 'Namespace of checkpoint expect to be a list')
        return Condition(inputs=inputs, func=config['method'],
                         output=config.get('output'))


class SkipAfterRequestLoader(_BaseLoader):
    _required_fields = ['conditions']

    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'SkipAfterRequest expect to be a dict')
        _check_required_fields(cls._required_fields, config)
        _ensure_list(config['conditions'], 'Conditions expect to be a list')

        sar = SkipAfterRequest()
        for item in config['conditions']:
            sar.add_condition(ConditionLoader.load(item))
        return sar


class RequestLoader(_BaseLoader):
    _required_fields = ['options', 'before_request', 'skip_after_request',
                        'after_request', 'checkpoint']

    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'Request expect to be a dict')
        _check_required_fields(cls._required_fields, config)

        options = OptionsLoader.load(config['options'])
        before_request = BeforeRequestLoader.load(config['before_request'])
        skip_after_request = SkipAfterRequestLoader.load(config['skip_after_request'])
        after_request = AfterRequestLoader.load(config['after_request'])
        checkpoint = CheckpointLoader.load(config['checkpoint'])

        return Request(options, before_request, skip_after_request,
                       after_request, checkpoint)


class CloudConnectConfigLoader(_BaseLoader):
    _required_fields = ['meta', 'parameters', 'requests']

    @classmethod
    def load(cls, config):
        _ensure_dict(config, 'JSON definition expect to be a dict')
        _check_required_fields(cls._required_fields, config)

        meta = MetaLoader.load(config['meta'])

        parameters = config['parameters']
        _ensure_list(parameters, 'Parameters expect to be a list')

        global_settings = GlobalSettingLoader.load(config.get('global_settings'))

        requests_as_list = config['requests']
        _ensure_list(requests_as_list, 'Requests expect to be a list')
        requests = [RequestLoader.load(item) for item in requests_as_list]

        return CloudConnectConfig(meta=meta, global_settings=global_settings,
                                  requests=requests)


def load_cloud_connect_config(json_file_path):
    """
    Load JSON based interface from a file path and validate it with schema.
    :param json_file_path: file path of json based interface.
    :return: A `CloudConnectConfig` object.
    """
    definition = _load_definition(json_file_path)
    validate(definition, _load_schema_from_file(_SCHEMA_LOCATION))
    return CloudConnectConfigLoader.load(definition)
