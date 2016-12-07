import base64
import logging

from httplib2 import (ProxyInfo, Http)
from .model.request import BasicAuthorization
from ..configuration import CloudConnectConfigLoaderV1
from ..splunktaucclib.common import log as stulog

_LOGGER = logging


class CloudConnectResponse(object):
    def __init__(self, res_headers, res_body):
        self._status_code = res_headers.status
        self._headers = res_headers
        self._body = res_body

    @property
    def headers(self):
        return self._headers

    @property
    def body(self):
        return self._body

    @property
    def status_code(self):
        return self._status_code


class CloudConnectClient(object):
    """
    The client of cloud connect used to start a cloud connect engine instance.
    """

    def __init__(self, context, config_file):
        self._context = context
        self._config_file = config_file

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
            request = CloudConnectRequest(request=item,
                                          context=self._context,
                                          proxy=config.global_settings.proxy)
            request.start()

        _LOGGER.info('All requests finished')


class CloudConnectRequest(object):
    """
    A class represents a single request instance.
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
        self._proxy = proxy
        self._url = None
        self._method = 'GET'
        self._headers = {}

    def _update_context(self, key, value):
        self._context[key] = value

    def _execute_tasks(self, tasks):
        if not tasks:
            return
        for task in tasks:
            self._context.update(task.execute(self._context))

    def _on_pre_process(self):
        """
        Execute tasks in pre process one by one.
        """
        tasks = self._request.pre_process.pipeline
        _LOGGER.info('Got %s tasks need be executed before process', len(tasks))
        self._execute_tasks(tasks)

    def _invoke_request(self):
        """
        Invoke a request with httplib2 and return it's response.
        :return: A response of request.
        """
        http = self._build_http_connection()
        uri = self._url
        body = None
        if "?" in self._url:
            uri, body = self._url.split("?")
        resp, content = http.request(uri, body=body, method=self._method,
                                     headers=self._headers)
        response = CloudConnectResponse(resp, content)
        return response

    def _on_post_process(self):
        tasks = self._request.post_process.pipeline
        _LOGGER.info('Got {} tasks need to be executed after process'.format(len(tasks)))
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

        while 1:
            self._init_request()
            self._on_pre_process()

            self._update_context('__response__', self._invoke_request())

            if not self._request.post_process.passed(self._context):
                self._on_post_process()
            if self._check_stop_condition():
                _LOGGER.info('Stop condition reached, exit loop now')
                break
            self._update_checkpoint()

        _LOGGER.info('Process request finished')

    def _build_http_connection(self, timeout=120,
                               disable_ssl_cert_validation=True):
        if self._proxy and self._proxy.enabled:
            proxy_info = ProxyInfo(proxy_type=self._proxy.type,
                                   proxy_host=self._proxy.host,
                                   proxy_port=self._proxy.port,
                                   proxy_user=self._proxy.username,
                                   proxy_pass=self._proxy.password,
                                   proxy_rdns=self._proxy.rdns)
            http = Http(proxy_info=proxy_info, timeout=timeout,
                        disable_ssl_certificate_validation=disable_ssl_cert_validation)
        else:
            http = Http(timeout=timeout,
                        disable_ssl_certificate_validation=disable_ssl_cert_validation)
        return http

    def _init_request(self):
        request_options = self._request.options
        self._url = request_options.url.value(self._context)
        self._method = request_options.method
        self._do_auth()
        self._handle_headers()

    def _handle_headers(self):
        options = self._request.options
        for key, value in options.header.iteritems():
            self._headers[key] = value.value(self._context)

    def _do_auth(self):
        options = self._request.options
        auth = options.auth
        if isinstance(auth, BasicAuthorization):
            username = auth.username.value(self._context)
            password = auth.password.value(self._context)
            encode_str = base64.encodestring(username + ':' + password)
            self._headers['Authorization'] = 'Basic ' + encode_str
