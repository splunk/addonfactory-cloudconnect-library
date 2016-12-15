import json
import threading
import traceback

from . import defaults
from .exceptions import HTTPError
from .http import HTTPRequest
from ..common import splunk_util
from ..common.log import get_cc_logger

_logger = get_cc_logger()


class CloudConnectEngine(object):
    """The cloud connect engine to process request instantiated
     from user options."""

    def __init__(self):
        self._stopped = False
        self._running_job = None
        self._running_thread = None

    @staticmethod
    def _set_logging(log_setting):
        _logger.set_level(log_setting.level)

    def start(self, context, config):
        """Start current client instance to execute each request parsed
         from config.
        """
        if not config:
            raise ValueError('Config must not be empty')

        self._running_thread = threading.current_thread()

        context = context or {}
        global_setting = config.global_settings

        CloudConnectEngine._set_logging(global_setting.logging)

        _logger.info('Start to execute requests jobs.')
        processed = 0

        for request in config.requests:
            job = Job(
                request=request, context=context, proxy=global_setting.proxy
            )
            self._running_job = job
            job.run()

            processed += 1
            _logger.info('%s job(s) process finished', processed)

            if self._stopped:
                _logger.info(
                    'Engine has been stopped, stopping to execute jobs.')
                break

        _logger.info('Engine executing finished')

    def stop(self):
        """Stops engine and running job. Do nothing if engine already
        been stopped."""
        if self._stopped:
            _logger.info('Engine already stopped, do nothing.')
            return

        _logger.info('Stopping engine')

        if self._running_job:
            self._running_job.stop()

        if self._running_thread \
                and self._running_thread != threading.current_thread():
            self._running_thread.join()

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
        """Sets job stopped flag to True"""
        _logger.info('Stopping job')
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
            _logger.info('Pre process condition not satisfied, do nothing')
            return

        tasks = pre_processor.pipeline
        _logger.debug(
            'Got %s tasks need be executed before process', len(tasks))
        self._execute_tasks(tasks)

    def _on_post_process(self):
        """
        Execute tasks in post process one by one if condition satisfied.
        """
        post_processor = self._request.post_process

        if post_processor.passed(self._context):
            _logger.info('Skip post process condition satisfied, '
                         'do nothing')
            return

        tasks = post_processor.pipeline
        _logger.debug(
            'Got %s tasks need to be executed after process', len(tasks)
        )
        self._execute_tasks(tasks)

    def _update_checkpoint(self):
        """Updates checkpoint based on checkpoint namespace and content."""
        checkpoint = self._request.checkpoint
        splunk_util.update_checkpoint(
            namespace=checkpoint.normalize_namespace(self._context),
            value=checkpoint.normalize_content(self._context)
        )

    def _get_checkpoint(self):
        checkpoint = splunk_util.get_checkpoint()
        if checkpoint:
            self._context.update(checkpoint)

    def _is_stoppable(self):
        repeat_mode = self._request.repeat_mode
        return repeat_mode.is_once() or repeat_mode.passed(self._context)

    def is_stopped(self):
        """Return if this job is stopped."""
        return self._stopped

    def run(self):
        """Start job and exit util meet stop condition. """
        _logger.info('Start to process job')

        try:
            self._run()
        except Exception as e:
            _logger.exception("engine encounter error")
            raise e

    def _run(self):
        _logger.info('Start to process request')

        options = self._request.options
        method = options.method
        authorizer = options.auth
        self._get_checkpoint()

        while 1:
            if self.is_stopped():
                _logger.info('Job has been stopped')
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
                    _logger.warn(
                        'Stop repeating request cause returned status %s on '
                        'sending request to [%s] with method [%s]: %s',
                        error.status, url, method, traceback.format_exc()
                    )
                    break
                _logger.error(
                    'Unexpected exception thrown on invoking request to [%s]'
                    ' with method [%s]: %s',
                    url, method, traceback.format_exc())
                raise

            if not response.body:
                _logger.warn(
                    'Stop repeating request cause request to url [%s]'
                    ' with method [%s] returned a empty response: '
                    '[%s]', url, method, response.body)
                break

            self._set_context('__response__', response)
            self._on_post_process()

            self._update_checkpoint()

            if self._is_stoppable():
                _logger.info('Stop condition reached, exit job now')
                break

            _logger.info('Job processing finished')
