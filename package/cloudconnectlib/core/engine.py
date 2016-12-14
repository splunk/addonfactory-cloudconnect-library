import json
import threading
import time

from . import defaults
from .exceptions import HTTPError
from .http import HTTPRequest
from ..common import log as _logger
from ..common import splunk_util


class CloudConnectEngine(object):
    """The cloud connect engine to process request instantiated
     from user options."""

    def __init__(self):
        self._stopped = False
        self._running_job = None
        self._running_thread = None

    @staticmethod
    def _set_logging(log_setting):
        _logger.set_log_level(log_setting.level)

    def start(self, context, config):
        """Start current client instance to execute each request parsed
         from config.
        """
        if not config:
            raise ValueError('Config must not be empty')

        self._running_thread = threading.current_thread()

        context = context or {}
        global_setting = config.global_settings

        self._set_logging(global_setting.logging)

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
                response, finished = \
                    self._do_request(url, method, header, body=rb)
            except Exception as error:
                if isinstance(error, HTTPError):
                    _logger.exception(
                        'HTTPError when sending request which url=%s, method=%s,'
                        ' status=%s',
                        url, method, error.status)
                else:
                    _logger.exception(
                        'Could not send request which url=%s, method=%s',
                        url, method)
                break

            if finished:
                break

            self._set_context('__response__', response)
            self._on_post_process()

            self._update_checkpoint()

            if self._is_stoppable():
                _logger.info('Stop condition reached, exit job now')
                break

            _logger.info('Job processing finished')

    def _do_request(self, url, method='GET', headers=None, body=None):
        """Do send request with a simple error handling strategy. For 5XX
        error we'll retry using an exponential backoff. Learn more from
        https://confluence.splunk.com/display/PROD/CC+1.0+-+Detail+Design"""
        retries = defaults.retries

        for i in xrange(retries):
            try:
                response = self._client.request(
                    url, method, headers, body=body)
            except HTTPError as e:
                if e.status and (e.status >= 500 or e.status == 429):
                    if i >= retries - 1:
                        raise

                    delay = 2 ** i
                    _logger.warning(
                        'Error status=%s responded when sending request'
                        ' which url=%s and method=%s. Retry after %s seconds.',
                        e.status, url, method, delay,
                    )

                    time.sleep(delay)
                    continue

                if e.status and 201 < e.status < 300:
                    _logger.warning(
                        'Error status=%s responded when sending request'
                        ' which url=%s and method=%s.'
                        ' The current interval is finished.',
                        e.status, url, method)
                    return None, True

                # status in [1XX, 3XX, 4XX]
                raise

            if not response.body:
                _logger.info(
                    'An empty response returned for request which url=%s and'
                    ' method=%s, status=%s.'
                    ' The current interval is finished.',
                    url, method, response.status_code
                )
                return None, True

            return response, False
