import json
import os.path as op

from jsonschema import validate, ValidationError
from ..core import util
from ..core.exception import InvalidConfigException
from ..core.model import (
    Meta, Proxy, Logging, GlobalSetting, Request, Header, Condition,
    Options, Checkpoint, BeforeRequest, AfterRequest, SkipAfterRequest,
    CloudConnectConfig, BasicAuthorization
)

# JSON schema file path.
_SCHEMA_LOCATION = op.join(op.dirname(__file__), 'hcm_schema.json')

_PROXY_TYPES = ['http', 'socks4', 'socks5', 'http_no_tunnel']
_AUTH_TYPE = {
    'basic_auth': BasicAuthorization
}


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
        raise InvalidConfigException(
            'Cannot load schema from {}'.format(file_path))


def _load_definition(file_path):
    """
    Load user's JSON interface definition from file.
    :param file_path: JSON interface file path.
    :return: A `dict` contains user defined JSON interface.
    """
    if not op.isfile(file_path):
        raise InvalidConfigException(
            'Invalid interface file {}'.format(file_path))
    try:
        return _json_file(file_path)
    except:
        raise InvalidConfigException(
            'Cannot load JSON interface from file {}'.format(file_path))


class _BaseLoader(object):
    """
    A base class for implementing a loader to load object from `dict`.
    """

    @classmethod
    def load(cls, candidate):
        pass


class MetaLoader(_BaseLoader):
    @classmethod
    def load(cls, candidate):
        return Meta(candidate)


class ProxyLoader(_BaseLoader):
    @classmethod
    def load(cls, candidate):
        if candidate is None:
            return None
        enabled = candidate['enabled']
        if not util.is_bool(enabled):
            raise InvalidConfigException('`enabled` of proxy is not bool')

        port = candidate['port']
        if not util.is_port(port):
            raise InvalidConfigException('proxy port is invalid: {}'.format(port))

        # proxy type default to `http`
        proxy_type = candidate.get('type')
        if proxy_type and proxy_type.lower() not in _PROXY_TYPES:
            raise InvalidConfigException('proxy type is invalid: {}'.format(proxy_type))

        return Proxy(enabled=enabled, host=candidate['host'], port=port,
                     type=proxy_type, rdns=candidate.get('rdns'))


class LoggingLoader(_BaseLoader):
    @classmethod
    def load(cls, candidate):
        if candidate is None:
            return None
        return Logging(level=candidate.get('level'))


class GlobalSettingLoader(_BaseLoader):
    _item_type = 'global_setting'

    @classmethod
    def load(cls, candidate):
        if candidate is None:
            return None
        proxy = ProxyLoader.load(candidate.get('proxy'))
        logging = LoggingLoader.load(candidate.get('logging'))
        return GlobalSetting(proxy=proxy, logging=logging)


class HeaderLoader(_BaseLoader):
    @classmethod
    def load(cls, header_item):
        header = Header()
        if header_item is None:
            return header
        for k, v in header_item:
            header.add(k, v)
        return header


class AuthorizationLoader(_BaseLoader):
    """
    A utility class for loading authorization class from `dict`.
    """

    @classmethod
    def load(cls, candidate):
        if candidate is None:
            return None
        auth_type = candidate['type'].lower()
        if auth_type not in _AUTH_TYPE:
            raise InvalidConfigException('unsupported auth type %s' % auth_type)
        auth_cls = _AUTH_TYPE[auth_type]
        return auth_cls(candidate['options'])


class OptionsLoader(_BaseLoader):
    @classmethod
    def load(cls, options):
        header = HeaderLoader.load(options.get('header'))
        return Options(header=header, method=options['method'],
                       url=options['url'], auth=options.get('auth'))


class CheckpointLoader(_BaseLoader):
    @classmethod
    def load(cls, checkpoint):
        namespace = checkpoint['namespace']
        content = checkpoint['content']
        return Checkpoint(namespace, content)


class BeforeRequestLoader(_BaseLoader):
    @classmethod
    def load(cls, before_requests):
        elements = []
        for item in before_requests:
            item_input = item['input']
            elements.append(BeforeRequest(item_input, item['method'],
                                          item.get('output')))
        return elements


class AfterRequestLoader(_BaseLoader):
    @classmethod
    def load(cls, after_requests):
        elements = []
        for item in after_requests:
            item_input = item['input']
            elements.append(AfterRequest(item_input, item['method'],
                                         item.get('output')))
        return elements


class ConditionLoader(_BaseLoader):
    @classmethod
    def load(cls, condition):
        inputs = condition['input']
        return Condition(inputs=inputs, func=condition['method'],
                         output=condition.get('output'))


class SkipAfterRequestLoader(_BaseLoader):
    @classmethod
    def load(cls, skip_after_request):
        conditions = skip_after_request['conditions']
        sar = SkipAfterRequest()
        for item in conditions:
            sar.add_condition(ConditionLoader.load(item))
        return sar


class RequestLoader(_BaseLoader):
    @classmethod
    def load(cls, requests):
        options = OptionsLoader.load(requests['options'])
        before_request = BeforeRequestLoader.load(requests['before_request'])
        skip_after_request = SkipAfterRequestLoader.load(requests['skip_after_request'])
        after_request = AfterRequestLoader.load(requests['after_request'])
        checkpoint = CheckpointLoader.load(requests['checkpoint'])

        return Request(options, before_request, skip_after_request,
                       after_request, checkpoint)


class CloudConnectConfigLoader(_BaseLoader):
    @classmethod
    def load(cls, config):
        meta = MetaLoader.load(config['meta'])
        parameters = config['parameters']
        global_settings = GlobalSettingLoader.load(config.get('global_settings'))
        requests = [RequestLoader.load(item) for item in config['requests']]

        return CloudConnectConfig(meta=meta, global_settings=global_settings,
                                  requests=requests)


def load_cloud_connect_config(json_file_path):
    """
    Load JSON based interface from a file path and validate it with schema.
    :param json_file_path: file path of json based interface.
    :return: A `CloudConnectConfig` object.
    """
    definition = _load_definition(json_file_path)
    try:
        validate(definition, _load_schema_from_file(_SCHEMA_LOCATION))
    except ValidationError:
        raise InvalidConfigException('Failed to validate interface with schema')

    return CloudConnectConfigLoader.load(definition)
