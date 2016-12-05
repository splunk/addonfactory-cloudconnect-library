import logging
import os.path as op
import traceback

from jinja2 import Template
from jsonschema import validate, ValidationError
from munch import munchify
from ..core import util
from ..core.exception import ConfigException
from ..core.model import (
    Request, CloudConnectConfigV1, BasicAuthorization, Options
)

# JSON schema file path.
_SCHEMA_LOCATION = op.join(op.dirname(__file__), 'hcm_schema.json')

_PROXY_TYPES = ['http', 'socks4', 'socks5', 'http_no_tunnel']
_AUTH_TYPES = {
    'basic_auth': BasicAuthorization
}

# Supported extended functions
_EXTEND_FUNCTIONS = ['json_path', 'json_empty', 'regex_not_match', 'regex_match', 'std_output']

_LOGGING_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'FATAL': logging.FATAL,
}


class CloudConnectConfigLoaderV1(object):
    _version = '1.0.0'

    @staticmethod
    def _load_schema_from_file(file_path):
        """
        Load JSON based schema definition from file.
        :param file_path: JSON based schema file path.
        :return: A `dict` contains schema.
        """
        try:
            return util.load_json_file(file_path)
        except:
            raise ConfigException('Cannot load schema from %s : %s'
                                  % (file_path, traceback.format_exc()))

    @staticmethod
    def _load_definition(file_path):
        """
        Load user's JSON interface definition from file.
        :param file_path: JSON interface file path.
        :return: A `dict` contains user defined JSON interface.
        """
        if not op.isfile(file_path):
            raise ConfigException(
                'Invalid interface file {}'.format(file_path))
        try:
            return util.load_json_file(file_path)
        except:
            raise ConfigException(
                'Cannot load JSON interface from file {}'.format(file_path))

    @staticmethod
    def _render_template(tpl, variables):
        return Template(tpl).render(variables)

    def _load_proxy(self, candidate, variables):
        if candidate is None:
            return None
        proxy = {k: self._render_template(v, variables)
                 for k, v in candidate.iteritems()}

        enabled = proxy['enabled']
        if not util.is_bool(enabled):
            raise ConfigException('proxy enabled expect to be bool type: {}'.
                                  format(enabled))

        port = proxy['port']
        if not util.is_port(port):
            raise ConfigException('proxy port expected to be in range [1,65535]: {}'.
                                  format(port))

        # proxy type default to 'http'
        proxy_type = proxy.get('type')
        if proxy_type and proxy_type.lower() not in _PROXY_TYPES:
            raise ConfigException('proxy type expect to be one of [{}]: {}'
                                  .format(','.join(_PROXY_TYPES), proxy_type))

        return proxy

    def _load_logging(self, log_setting, variables):
        log_setting = log_setting or {}
        log = {k: self._render_template(v, variables)
               for k, v in log_setting.iteritems()}
        level = log.get('level', '').upper()
        log['level'] = _LOGGING_LEVELS.get(level, logging.INFO)
        return log

    def _load_global_setting(self, candidate, variables):
        """
        Load and render global setting with variables.
        :param candidate: Global setting as a `dict`
        :param variables: variables from context to render setting
        :return: A `Munch` object
        """
        candidate = candidate or {}
        proxy_setting = self._load_proxy(candidate.get('proxy'), variables)
        log_setting = self._load_logging(candidate.get('logging'), variables)

        candidate.update({'proxy': proxy_setting,
                          'logging': log_setting})
        return munchify(candidate)

    @staticmethod
    def _load_authorization(candidate):
        if candidate is None:
            return None
        auth_type = candidate['type'].lower()
        if auth_type not in _AUTH_TYPES:
            raise ConfigException('auth type expect to be one of [{}]: {}'
                                  .format(','.join(_AUTH_TYPES), auth_type))
        auth_cls = _AUTH_TYPES[auth_type]
        return auth_cls(candidate['options'])

    def _load_options(self, options):
        return Options(auth=self._load_authorization(options.get('auth')),
                       url=options['url'],
                       method=options['method'],
                       header=munchify(options.get('headers')))

    @staticmethod
    def _validate_ext_method(tasks):
        for task in tasks:
            if task.method not in _EXTEND_FUNCTIONS:
                raise ConfigException(
                    'method expect to be one of [{}]: {}'.format(
                        ','.join(_EXTEND_FUNCTIONS), task.method))

    def _load_request(self, request):
        before_request = munchify(request['before_request'])
        self._validate_ext_method(before_request)

        skip_after_request = munchify(request['skip_after_request'])
        self._validate_ext_method(skip_after_request.conditions)

        after_request = munchify(request['after_request'])
        self._validate_ext_method(after_request)

        return Request(options=self._load_options(request['options']),
                       before_request=before_request,
                       skip_after_request=skip_after_request,
                       after_request=after_request,
                       checkpoint=munchify(request['checkpoint']),
                       loop_mode=munchify(request['loop_mode']))

    def _check_version(self, version):
        if version != self._version:
            raise ConfigException(
                'unsupported schema version {}, current supported versions '
                '{}'.format(version, self._version))

    def load_config(self, json_file_path, context):
        """
        Load JSON based interface from a file path and validate it with schema.
        :param context: variables to render template in global setting.
        :param json_file_path: file path of json based interface.
        :return: A `CloudConnectConfigV1` object.
        """
        definition = self._load_definition(json_file_path)
        try:
            validate(definition, self._load_schema_from_file(_SCHEMA_LOCATION))
        except ValidationError:
            raise ConfigException('Failed to validate interface with schema: '
                                  '{}'.format(traceback.format_exc()))

        meta = munchify(definition['meta'])
        self._check_version(meta.version)

        parameters = definition['parameters']

        global_settings = self._load_global_setting(
            definition.get('global_settings'), context)
        requests = [self._load_request(item) for item in definition['requests']]

        return CloudConnectConfigV1(meta=meta,
                                    parameters=parameters,
                                    global_settings=global_settings,
                                    requests=requests)
