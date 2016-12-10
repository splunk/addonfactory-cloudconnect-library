import json
import logging
import traceback

from . import defaults
from .exceptions import HTTPError
from .http import HTTPRequest
from ..splunktacollectorlib.common import log as stulog

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging


class CloudConnectEngine(object):
    """The cloud connect engine to process request instantiated
     from user options."""

    def __init__(self):
        self._stopped = False
        self._running_job = None

    @staticmethod
    def _set_logging(log_setting):
        stulog.set_log_level(log_setting.level)

    def start(self, context, config):
        """Start current client instance to execute each request parsed
         from config.
        """
        if not config:
            raise ValueError('Config must not be empty')

        context = context or {}
        global_setting = config.global_settings

        self._set_logging(global_setting.logging)

        _LOGGER.info('Start to execute request jobs')
        processed = 0

        for request in config.requests:
            job = Job(
                request=request, context=context, proxy=global_setting.proxy
            )
            self._running_job = job
            job.run()

            processed += 1
            _LOGGER.info('%s job(s) process finished', processed)

            if self._stopped:
                _LOGGER.info(
                    'Engine has been stopped, stopping to execute jobs.')
                break

        _LOGGER.info('Engine executing finished')

    def stop(self):
        if self._stopped:
            _LOGGER.info('Engine already stopped, do nothing.')
            return

        _LOGGER.info('Stopping engine')

        if self._running_job:
            self._running_job.stop()
        self._stopped = True


class Job(object):
    """Job class represents a single request to send HTTP request until
    reached it's stop condition.
    """

    def __init__(self, request, context, proxy=None):
        """
        Constructs a `Job` with properties request, context and a
         optional proxy setting.
        :param request: A `Request` instance which contains request settings.
        :param context: A values set contains initial values for template
         variables.
        :param proxy: A optional `Proxy` object contains proxy related
         settings.
        """
        self._request = request
        self._context = context
        self._client = HTTPRequest(proxy)
        self._stopped = False

    def stop(self):
        _LOGGER.info('Stopping job')
        self._stopped = True

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

    def _is_stoppable(self):
        repeat_mode = self._request.repeat_mode
        return repeat_mode.is_once() or repeat_mode.passed(self._context)

    def is_stopped(self):
        """Return if this job is stopped."""
        return self._stopped

    def run(self):
        """Start job and exit util meet stop condition. """
        _LOGGER.info('Start to process job')

        options = self._request.options
        method = options.method
        authorizer = options.auth

        while 1:
            if self.is_stopped():
                _LOGGER.info('Job has been stopped')
                break

            url = options.normalize_url(self._context)
            header = options.normalize_header(self._context)
            body = options.normalize_body(self._context)
            rb = json.dumps(body) if body else None

            if authorizer:
                authorizer(header, self._context)

            self._on_pre_process()

            try:
                response = self._client.request(url, method, header, body=rb)
            except HTTPError as error:
                if error.status in defaults.exit_status:
                    _LOGGER.warn(
                        'Stop repeating request cause returned status %s on '
                        'sending request to [%s] with method [%s]: %s',
                        error.status, url, method, traceback.format_exc()
                    )
                    break
                _LOGGER.error(
                    'Unexpected exception thrown on invoking request to [%s]'
                    ' with method [%s]: %s',
                    url, method, traceback.format_exc())
                raise

            if not response.body:
                _LOGGER.warn(
                    'Stop repeating request cause request to url [%s]'
                    ' with method [%s] returned a empty response: '
                    '[%s]', url, method, response.body)
                break

            self._set_context('__response__', response)
            self._on_post_process()

            self._update_checkpoint()

            if self._is_stoppable():
                _LOGGER.info('Stop condition reached, exit job now')
                break

        _LOGGER.info('Job processing finished')
