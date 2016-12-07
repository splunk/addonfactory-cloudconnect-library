import logging
import traceback

from .exceptions import HTTPError
from .http import HTTPRequest
from ..configuration import CloudConnectConfigLoaderV1
from ..splunktaucclib.common import log as stulog

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging


class CloudConnectClient(object):
    """
    The client of cloud connect used to start a cloud connect engine instance.
    """

    def __init__(self, context, config_file):
        self._context = context
        self._config_file = config_file
        self._stopped = False

    @staticmethod
    def _set_logging(log_setting):
        stulog.set_log_level(log_setting.level)

    def run(self):
        """
        Start current client instance to execute each request parsed from config.
        """
        config_loader_v1 = CloudConnectConfigLoaderV1()
        config = config_loader_v1.load_config(self._config_file, self._context)

        global_setting = config.global_settings
        self._set_logging(global_setting.logging)

        _LOGGER.info('Start to execute requests')

        for item in config.requests:
            job = Job(request=item, context=self._context,
                      proxy=global_setting.proxy)
            job.start()

        _LOGGER.info('All requests finished')

    def stop(self):
        pass


class Job(object):
    """
    HTTPRequest class represents a single request to send HTTP request until
    reached it's stop condition.
    """

    def __init__(self, request, context, proxy=None):
        """
        Constructs a `CloudConnectRequest` with properties request, contenxt
        and a optional proxy setting.
        :param request: A `Request` instance which contains request settings.
        :param context: A values set contains initial values for template variables.
        :param proxy: A optional `Proxy` object contains proxy related settings.
        """
        self._request = request
        self._context = context
        self._client = HTTPRequest(proxy)

    def _set_context(self, key, value):
        self._context[key] = value

    def _execute_tasks(self, tasks):
        if not tasks:
            return
        for task in tasks:
            self._context.update(task.execute(self._context))

    def _on_pre_process(self):
        """
        Execute tasks in pre process one by one if condition satisfied.
        """
        pre_processor = self._request.pre_process

        if not pre_processor.passed(self._context):
            _LOGGER.info('Pre process condition not satisfied, do nothing')
            return

        tasks = pre_processor.pipeline
        _LOGGER.debug(
            'Got %s tasks need be executed before process', len(tasks))
        self._execute_tasks(tasks)

    def _on_post_process(self):
        """
        Execute tasks in post process one by one if condition satisfied.
        """
        post_processor = self._request.post_process

        if not post_processor.passed(self._context):
            _LOGGER.info('Post process condition not satisfied, do nothing')
            return

        tasks = post_processor.pipeline
        _LOGGER.debug(
            'Got %s tasks need to be executed after process', len(tasks)
        )
        self._execute_tasks(tasks)

    def _update_checkpoint(self):
        # TODO
        pass

    def _check_stop_condition(self):
        repeat_mode = self._request.repeat_mode
        return repeat_mode.is_once() or repeat_mode.passed(self._context)

    def start(self):
        """
        Start request instance and exit util meet stop condition.
        """
        _LOGGER.info('Start to process request')
        options = self._request.options
        method = options.method
        authorizer = options.auth

        while 1:
            url = options.normalize_url(self._context)
            header = options.normalize_header(self._context)
            body = options.normalize_body(self._context)

            if authorizer:
                authorizer(header, self._context)

            self._on_pre_process()

            try:
                response = self._client.request(url, method, header, body)
            except HTTPError as error:
                if error.status == 404:
                    _LOGGER.warn(
                        'Stop repeating request cause request returned 404 error')
                    break
                _LOGGER.error(
                    'Unexpected exception thrown on invoking request: %s',
                    traceback.format_exc())
                raise

            if not response.body:
                _LOGGER.warn('Stop repeating request cause request returned'
                             ' a empty response: [%s]', response.body)
                break

            self._set_context('__response__', response)
            self._on_post_process()

            if self._check_stop_condition():
                _LOGGER.info('Stop condition reached, exit job now')
                break
            self._update_checkpoint()

        _LOGGER.info('Process request finished')
