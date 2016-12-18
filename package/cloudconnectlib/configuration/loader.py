import logging
import re
import traceback
from abc import abstractmethod

from jsonschema import validate, ValidationError
from munch import munchify
from ..common.log import get_cc_logger
from ..common.util import (
    load_json_file, is_valid_bool, is_valid_port, is_true
)
from ..core.exceptions import ConfigException
from ..core.ext import lookup_method
from ..core.models import (
    BasicAuthorization, Options, Processor,
    Condition, Task, Checkpoint, IterationMode
)
from ..core.template import compile_template

_logger = get_cc_logger()

_PROXY_TYPES = ['http', 'socks4', 'socks5', 'http_no_tunnel']
_AUTH_TYPES = {
    'basic_auth': BasicAuthorization
}

_LOGGING_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'ERROR': logging.ERROR,
    'FATAL': logging.FATAL,
}


class CloudConnectConfigLoader(object):
    """The Base cloud connect configuration loader"""

    @staticmethod
    def _get_schema_from_file(schema_file):
        """ Load JSON based schema definition from schema file path.
        :return: A `dict` contains schema.
        """
        try:
            return load_json_file(schema_file)
        except:
            raise ConfigException(
                'Cannot load schema from {}: {}'.format(
                    schema_file, traceback.format_exc())
            )

    @abstractmethod
    def load(self, definition, schema_file, context):
        pass


class CloudConnectConfigLoaderV1(CloudConnectConfigLoader):
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
        proxy = {k: self._render_template(v, variables).strip()
                 for k, v in candidate.iteritems()}

        enabled = proxy.get('enabled', '0')
        if not is_valid_bool(enabled):
            raise ValueError(
                'Proxy enabled expect to be bool type: {}'.format(enabled))
        else:
            proxy['enabled'] = is_true(enabled)

        port = proxy['port']
        if proxy['host'] and not is_valid_port(port):
            raise ValueError(
                'Proxy port expect to be in range [1,65535]: {}'.format(port)
            )

        # proxy type default to 'http'
        proxy_type = proxy.get('type')
        proxy_type = proxy_type.lower() if proxy_type else 'http'
        if proxy_type not in _PROXY_TYPES:
            raise ValueError(
                'Proxy type expect to be one of [{}]: {}'.format(
                    ','.join(_PROXY_TYPES), proxy_type)
            )
        else:
            proxy['type'] = proxy_type

        # proxy rdns default to '0'
        proxy_rdns = proxy.get('rdns', '0')
        if not is_valid_bool(proxy_rdns):
            raise ValueError(
                'Proxy rdns expect to be bool type: {}'.format(proxy_rdns))
        else:
            proxy['rdns'] = is_true(proxy_rdns)

        return proxy

    def _load_logging(self, log_setting, variables):
        log_setting = log_setting or {}
        logger = {k: self._render_template(v, variables)
                  for k, v in log_setting.iteritems()}

        level = logger.get('level', '').upper()

        if level not in _LOGGING_LEVELS:
            _logger.warning('Log level not specified, set log level to INFO')
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
            raise ValueError(
                'Auth type expect to be one of [{}]: {}'.format(
                    ','.join(_AUTH_TYPES.keys()), auth_type)
            )
        return _AUTH_TYPES[auth_type](candidate['options'])

    def _load_options(self, options):
        return Options(auth=self._load_authorization(options.get('auth')),
                       url=options['url'],
                       method=options['method'],
                       header=options.get('headers', {}),
                       body=options.get('body', {}))

    @staticmethod
    def _validate_method(method):
        if lookup_method(method) is None:
            raise ValueError('Unimplemented method: {}'.format(method))

    def _parse_tasks(self, raw_tasks):
        tasks = []
        for item in raw_tasks:
            self._validate_method(item['method'])
            tasks.append(Task(item['input'], item['method'], item.get('output')))
        return tasks

    def _parse_conditions(self, raw_conditions):
        conditions = []
        for item in raw_conditions:
            self._validate_method(item['method'])
            conditions.append(Condition(item['input'], item['method']))
        return conditions

    @staticmethod
    def _load_checkpoint(checkpoint):
        return Checkpoint(
            checkpoint.get('namespace', []), checkpoint['content'])

    def _load_iteration_mode(self, iteration_mode):
        count = iteration_mode.get('iteration_count', '0')
        try:
            iteration_count = int(count)
        except ValueError:
            raise ValueError(
                'Iteration mode "iteration_count" must be an integer: %s' % count)

        stop_conditions = self._parse_conditions(
            iteration_mode['stop_conditions'])

        return IterationMode(iteration_count=iteration_count,
                             conditions=stop_conditions)

    def _load_processor(self, processor):
        skip_conditions = self._parse_conditions(
            processor.get('skip_conditions', [])
        )
        pipeline = self._parse_tasks(processor.get('pipeline', []))
        return Processor(
            skip_conditions=skip_conditions,
            pipeline=pipeline
        )

    def _load_request(self, request):
        options = self._load_options(request['options'])
        pre_process = self._load_processor(request['pre_process'])
        post_process = self._load_processor(request['post_process'])
        checkpoint = self._load_checkpoint(request['checkpoint'])
        iteration_mode = self._load_iteration_mode(request['iteration_mode'])

        return munchify({
            'options': options,
            'pre_process': pre_process,
            'post_process': post_process,
            'checkpoint': checkpoint,
            'iteration_mode': iteration_mode,
        })

    def load(self, definition, schema_file, context):
        """Load cloud connect configuration from a `dict` and validate
        it with schema and global settings will be rendered.
        :param schema_file: Schema file location used to validate config.
        :param definition: A dictionary contains raw configs.
        :param context: variables to render template in global setting.
        :return: A `Munch` object.
        """
        try:
            validate(definition, self._get_schema_from_file(schema_file))
        except ValidationError:
            raise ConfigException(
                'Failed to validate interface with schema: {}'.format(
                    traceback.format_exc()))

        try:
            global_settings = self._load_global_setting(
                definition.get('global_settings'), context)

            requests = [self._load_request(item) for item in definition['requests']]

            return munchify({
                'meta': munchify(definition['meta']),
                'tokens': definition['tokens'],
                'global_settings': global_settings,
                'requests': requests,
            })
        except (TypeError, ValueError):
            _logger.exception('Unable to parse config')
            raise ConfigException('Unable to load configuration')


_loader_and_schema_by_version = {
    r'1\.0\.0': (CloudConnectConfigLoaderV1, 'schema_1_0_0.json'),
}


def get_loader_by_version(version):
    """ Instantiate a configuration loader on basis of a given version.
    A `ConfigException` will raised if the version is not supported.
    :param version: Version to lookup config loader.
    :return: A config loader.
    """
    for support_version in _loader_and_schema_by_version:
        if re.match(support_version, version):
            loader_cls, schema = _loader_and_schema_by_version[support_version]
            return loader_cls(), schema

    raise ConfigException(
        'Unsupported schema version {}, current supported'
        ' versions should match these regex [{}]'.format(version, ','.join(
            _loader_and_schema_by_version))
    )
