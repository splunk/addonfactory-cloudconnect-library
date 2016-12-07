import logging
import os.path as op
import traceback

from jsonschema import validate, ValidationError
from munch import munchify
from ..core import util
from ..core.exception import ConfigException
from ..core.ext import lookup
from ..core.model import (
    CloudConnectConfigV1, BasicAuthorization, Request, Options, Processor,
    Condition, Task, Checkpoint, RepeatMode
)
from ..core.template import compile_template
from ..splunktalib.common import log

# JSON schema file path.
_SCHEMA_LOCATION = op.join(op.dirname(__file__), 'schema.json')

_PROXY_TYPES = ['http', 'socks4', 'socks5', 'http_no_tunnel']
_AUTH_TYPES = {
    'basic_auth': BasicAuthorization
}

_REPEAT_MODE_TYPES = ['loop', 'once']

_LOGGING_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'FATAL': logging.FATAL,
}

_LOGGER = log.Logs().get_logger('cloud_connect')


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
            raise ConfigException('Cannot load schema from {}: {}'
                                  .format(file_path, traceback.format_exc()))

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
                'Cannot load JSON interface from file {}: {}'.format(
                    file_path, traceback.format_exc()))

    @staticmethod
    def _render_template(template, variables):
        return compile_template(template)(variables)

    def _load_proxy(self, candidate, variables):
        """
        Render and validate proxy setting with given variables.
        :param candidate: raw proxy setting as `dict`
        :param variables: variables to render template in proxy setting.
        :return: A `dict` contains rendered proxy setting.
        """
        if candidate is None:
            return None
        proxy = {k: self._render_template(v, variables)
                 for k, v in candidate.iteritems()}

        enabled = proxy.get('enabled', '0')
        if not util.is_bool(enabled):
            raise ConfigException('proxy enabled expect to be bool type: {}'.
                                  format(enabled))
        else:
            proxy['enabled'] = util.is_true(enabled)

        port = proxy['port']
        if not util.is_port(port):
            raise ConfigException('proxy port expected to be in range [1,65535]: {}'.
                                  format(port))

        # proxy type default to 'http'
        proxy_type = proxy.get('type', 'http').lower()
        if proxy_type not in _PROXY_TYPES:
            raise ConfigException('proxy type expect to be one of [{}]: {}'
                                  .format(','.join(_PROXY_TYPES), proxy_type))
        else:
            proxy['type'] = proxy_type

        # proxy rdns default to '0'
        proxy_rdns = proxy.get('rdns', '0')
        if not util.is_bool(proxy_rdns):
            raise ConfigException('proxy rdns expect to be bool type: {}'.
                                  format(proxy_rdns))
        else:
            proxy['rdns'] = util.is_true(proxy_rdns)
        return proxy

    def _load_logging(self, log_setting, variables):
        log_setting = log_setting or {}
        logger = {k: self._render_template(v, variables)
                  for k, v in log_setting.iteritems()}

        level = logger.get('level', '').upper()

        if level not in _LOGGING_LEVELS:
            _LOGGER.warn('Log level not specified, set log level to INFO')
            logger['level'] = logging.INFO
        else:
            logger['level'] = _LOGGING_LEVELS[level]
        return logger

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

        return munchify({'proxy': proxy_setting, 'logging': log_setting})

    @staticmethod
    def _load_authorization(candidate):
        if candidate is None:
            return None
        auth_type = candidate['type'].lower()

        if auth_type not in _AUTH_TYPES:
            raise ConfigException('auth type expect to be one of [{}]: {}'
                                  .format(','.join(_AUTH_TYPES.keys()), auth_type))
        return _AUTH_TYPES[auth_type](candidate['options'])

    def _load_options(self, options):
        return Options(auth=self._load_authorization(options.get('auth')),
                       url=options['url'],
                       method=options['method'],
                       header=options.get('headers', {}),
                       body=options.get('body', {}))

    @staticmethod
    def _validate_ext_method(method):
        if lookup(method) is None:
            raise ConfigException('unimplemented method: {}'.format(method))

    def _parse_tasks(self, raw_tasks):
        tasks = []
        for item in raw_tasks:
            self._validate_ext_method(item['method'])
            tasks.append(Task(item['input'], item['method'], item.get('output')))
        return tasks

    def _parse_conditions(self, raw_conditions):
        conditions = []
        for item in raw_conditions:
            self._validate_ext_method(item['method'])
            conditions.append(Condition(item['input'], item['method']))
        return conditions

    @staticmethod
    def _load_checkpoint(checkpoint):
        return Checkpoint(checkpoint['namespace'], checkpoint['content'])

    def _load_repeat_mode(self, repeat_mode):
        loop_type = repeat_mode.get('type')

        if not loop_type or loop_type.lower() not in _REPEAT_MODE_TYPES:
            _LOGGER.warn('loop mode type expect to be one of [{}]: found {},'
                         ' setting to default type'
                         .format(','.join(_REPEAT_MODE_TYPES), loop_type))
            loop_type = 'once'
        else:
            loop_type = loop_type.lower()

        stop_conditions = self._parse_conditions(repeat_mode['stop_conditions'])

        return RepeatMode(loop_type, stop_conditions)

    def _load_processor(self, processor):
        conditions = self._parse_conditions(processor.get('conditions', []))
        tasks = self._parse_tasks(processor.get('pipeline', []))
        return Processor(conditions=conditions, pipeline=tasks)

    def _load_request(self, request):
        options = self._load_options(request['options'])
        pre_process = self._load_processor(request['pre_process'])
        post_process = self._load_processor(request['post_process'])
        ckpt = self._load_checkpoint(request['checkpoint'])
        repeat_mode = self._load_repeat_mode(request['repeat_mode'])

        return Request(options=options,
                       pre_process=pre_process,
                       post_process=post_process,
                       checkpoint=ckpt,
                       repeat_mode=repeat_mode)

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
