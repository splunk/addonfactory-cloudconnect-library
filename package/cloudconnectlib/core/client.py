import base64
import logging

from httplib2 import (ProxyInfo, Http)
from .ext import lookup
from .model.request import BasicAuthorization
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

    def __init__(self, context, config):
        self._context = context
        self._config = config

    @staticmethod
    def _set_logging(logging):
        stulog.set_log_level(logging.level)

    def run(self):
        """
        Start current client instance to execute each request parsed from config.
        """
        # config = load_cloud_connect_config(self._config_file)
        global_setting = self._config.global_settings
        self._set_logging(global_setting.logging)

        _LOGGER.info('Start to execute requests')

        for item in self._config.requests:
            request = CloudConnectRequest(request=item,
                                          context=self._context,
                                          proxy=self._config.global_settings.proxy)
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
        for task in tasks:
            func = lookup(task.method)
            if func is None:
                raise ValueError("method {} doesn't exist".format(task.method))
            output_attr = task.output
            args = [arg for arg in task.inputs_values(self._context)]

            if output_attr is None:
                func(*args)
            else:
                self._update_context(output_attr, func(*args))

    def _do_stuff_before_request(self):
        """
        Execute tasks in before request one by one.
        """
        before_request_tasks = self._request.before_request
        if before_request_tasks:
            _LOGGER.info('Got {} tasks in before request'
                         .format(len(before_request_tasks)))
            self._execute_tasks(before_request_tasks)
            return
        _LOGGER.info("No before request task need to execute")

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

    def _skip_after_request(self):
        """
        Determine if we need to skip the step of after request based on the
        response content.
        :return: `True` if don't need process after request else `False`.
        """
        conditions = self._request.skip_after_request.conditions
        return all(item.calculate(self._context) for item in conditions)

    def _do_stuff_after_request(self):
        tasks = self._request.after_request
        if tasks:
            _LOGGER.info('Got {} tasks in after request'.format(len(tasks)))
            self._execute_tasks(tasks)
            return
        _LOGGER.info("No after request task need to execute")

    def _update_checkpoint(self):
        pass

    def _check_stop_condition(self):
        loop_mode = self._request.loop_mode
        if loop_mode.is_once():
            return True
        return all(condition.calculate(self._context)
                   for condition in loop_mode.conditions)

    def start(self):
        """
        Start request instance and exit util meet stop condition.
        """
        _LOGGER.info('Start to process request')

        while 1:
            self._init_request()
            self._do_stuff_before_request()

            self._update_context('__response__', self._invoke_request())

            if not self._skip_after_request():
                self._do_stuff_after_request()
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
        self._url = request_options.url.render_value(self._context)
        self._method = request_options.method
        self._do_auth()
        self._handle_headers()

    def _handle_headers(self):
        options = self._request.options
        header_item = options.header.items
        for key, value in header_item.iteritems():
            self._headers[key] = value.render_value(self._context)

    def _do_auth(self):
        options = self._request.options
        auth = options.auth
        if isinstance(auth, BasicAuthorization):
            username = auth.username.render_value(self._context)
            password = auth.password.render_value(self._context)
            encode_str = base64.encodestring(username + ':' + password)
            self._headers['Authorization'] = 'Basic ' + encode_str
