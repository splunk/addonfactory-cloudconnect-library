import json
import os.path as op

from jsonschema import validate
from ..core import util
from ..core.model import (
    Meta, Proxy, Logging, GlobalSetting, Request, Header, Condition,
    Options, Checkpoint, BeforeRequest, AfterRequest, SkipAfterRequest,
    CloudConnectConfig
)

# JSON schema file path.
_SCHEMA_LOCATION = op.join(op.dirname(__file__), 'hcm_schema.json')

_PROXY_TYPES = ['http', 'socks4', 'socks5', 'http_no_tunnel']
_HTTP_METHODS = ['HTTP', 'POST']


def _check_type(candidate, expect_type, item_type):
    if not isinstance(candidate, expect_type):
        raise TypeError('{} is not a {}'.format(item_type, expect_type))


def _check_required_fields(fields, candidate, item):
    for f in fields:
        if f not in candidate:
            raise ValueError('{} of {} is required'.format(f, item))


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


class MetaLoader(_BaseLoader):
    _required_fields = ['version']
    _item_type = 'meta'

    @classmethod
    def load(cls, candidate):
        _check_type(candidate, dict, cls._item_type)
        _check_required_fields(cls._required_fields, candidate, cls._item_type)
        return Meta(candidate)


class ProxyLoader(_BaseLoader):
    _required_fields = ['enabled', 'host', 'port']
    _item_type = 'proxy'

    @classmethod
    def load(cls, candidate):
        if candidate is None:
            return None
        _check_type(candidate, dict, cls._item_type)
        _check_required_fields(cls._required_fields, candidate, cls._item_type)

        enabled = candidate['enabled']
        if not util.is_bool(enabled):
            raise ValueError('`enabled` of proxy is not bool')

        port = candidate['port']
        if not util.is_port(port):
            raise ValueError('proxy port is invalid: {}'.format(port))

        # proxy type default to `http`
        proxy_type = candidate.get('type')
        if proxy_type and proxy_type not in _PROXY_TYPES:
            raise ValueError('proxy type is invalid: {}'.format(proxy_type))

        return Proxy(enabled=enabled, host=candidate['host'], port=port,
                     type=proxy_type, rdns=candidate.get('rdns'))


class LoggingLoader(_BaseLoader):
    _item_type = 'logging'

    @classmethod
    def load(cls, candidate):
        if candidate is None:
            return None
        _check_type(candidate, dict, cls._item_type)
        return Logging(level=candidate.get('level'))


class GlobalSettingLoader(_BaseLoader):
    _item_type = 'global_setting'

    @classmethod
    def load(cls, candidate):
        if candidate is None:
            return None
        _check_type(candidate, dict, cls._item_type)

        proxy = ProxyLoader.load(candidate.get('proxy'))
        logging = LoggingLoader.load(candidate.get('logging'))
        return GlobalSetting(proxy=proxy, logging=logging)


class HeaderLoader(_BaseLoader):
    _item_type = 'header'

    @classmethod
    def load(cls, header_item):
        header = Header()
        if header_item is None:
            return header
        _check_type(header_item, dict, cls._item_type)
        for k, v in header_item:
            header.add(k, v)
        return header


class OptionsLoader(_BaseLoader):
    _required_fields = ['url', 'method', 'header']
    _item_type = 'options'

    @classmethod
    def load(cls, options):
        _check_type(options, dict, cls._item_type)
        _check_required_fields(cls._required_fields, options, cls._item_type)

        header = HeaderLoader.load(options.get('header'))

        method = options['method'].upper()
        if method not in _HTTP_METHODS:
            raise ValueError('http method is invalid {}'.format(method))

        return Options(header=header, method=options['method'],
                       url=options['url'], auth=options.get('auth'))


class CheckpointLoader(_BaseLoader):
    _required_fields = ['namespace', 'content']
    _item_type = 'checkpoint'

    @classmethod
    def load(cls, checkpoint):
        _check_type(checkpoint, dict, cls._item_type)
        _check_required_fields(cls._required_fields, checkpoint, cls._item_type)

        namespace = checkpoint['namespace']
        _check_type(namespace, list, 'checkpoint namespace')
        content = checkpoint['content']
        _check_type(content, list, 'checkpoint content')

        return Checkpoint(namespace, content)


class BeforeRequestLoader(_BaseLoader):
    _required_fields = ['input', 'method']
    _item_type = 'before_request'

    @classmethod
    def load(cls, before_requests):
        _check_type(before_requests, list, cls._item_type)

        elements = []
        for item in before_requests:
            _check_type(item, dict, 'before request')
            _check_required_fields(cls._required_fields, item, 'before request')

            item_input = item['input']
            _check_type(item_input, list, 'before request input')

            elements.append(BeforeRequest(item_input, item['method'],
                                          item.get('output')))
        return elements


class AfterRequestLoader(_BaseLoader):
    _required_fields = ['input', 'method']
    _item_type = 'after_request'

    @classmethod
    def load(cls, after_requests):
        _check_type(after_requests, list, cls._item_type)

        elements = []
        for item in after_requests:
            _check_type(item, dict, 'after request')
            _check_required_fields(cls._required_fields, item, 'after request')

            item_input = item['input']
            _check_type(item_input, list, 'after request input')

            elements.append(AfterRequest(item_input, item['method'],
                                         item.get('output')))
        return elements


class ConditionLoader(_BaseLoader):
    _required_fields = ['input', 'method']
    _item_type = 'condition'

    @classmethod
    def load(cls, condition):
        _check_type(condition, dict, cls._item_type)
        _check_required_fields(cls._required_fields, condition, cls._item_type)

        inputs = condition['input']
        _check_type(inputs, list, 'condition input')

        return Condition(inputs=inputs, func=condition['method'],
                         output=condition.get('output'))


class SkipAfterRequestLoader(_BaseLoader):
    _required_fields = ['conditions']
    _item_type = 'skip_after_request'

    @classmethod
    def load(cls, skip_after_request):
        _check_type(skip_after_request, dict, cls._item_type)
        _check_required_fields(cls._required_fields, skip_after_request, cls._item_type)

        conditions = skip_after_request['conditions']
        _check_type(conditions, list, 'skip after request conditions')

        sar = SkipAfterRequest()
        for item in conditions:
            sar.add_condition(ConditionLoader.load(item))
        return sar


class RequestLoader(_BaseLoader):
    _required_fields = ['options', 'before_request', 'skip_after_request',
                        'after_request', 'checkpoint']
    _item_type = 'request'

    @classmethod
    def load(cls, requests):
        _check_type(requests, list, cls._item_type)
        _check_required_fields(cls._required_fields, requests, cls._item_type)

        options = OptionsLoader.load(requests['options'])
        before_request = BeforeRequestLoader.load(requests['before_request'])
        skip_after_request = SkipAfterRequestLoader.load(requests['skip_after_request'])
        after_request = AfterRequestLoader.load(requests['after_request'])
        checkpoint = CheckpointLoader.load(requests['checkpoint'])

        return Request(options, before_request, skip_after_request,
                       after_request, checkpoint)


class CloudConnectConfigLoader(_BaseLoader):
    _required_fields = ['meta', 'parameters', 'requests']
    _item_type = 'cloud_connect_config'

    @classmethod
    def load(cls, config):
        _check_type(config, dict, cls._item_type)
        _check_required_fields(cls._required_fields, config, cls._item_type)

        meta = MetaLoader.load(config['meta'])
        parameters = config['parameters']
        _check_type(parameters, list, 'parameters')

        global_settings = GlobalSettingLoader.load(config.get('global_settings'))

        requests = config['requests']
        _check_type(requests, list, 'requests')
        requests = [RequestLoader.load(item) for item in requests]

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
