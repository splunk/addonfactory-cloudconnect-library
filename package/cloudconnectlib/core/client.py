from ..configuration.loaders import load_cloud_connect_config
from ..splunktalib.common import log
from ..splunktalib.rest import build_http_connection
from ..splunktaucclib.common import log as stulog

_LOGGER = log.Logs().get_logger('cloud_connect')


class CloudConnectClient(object):
    """
    The client of cloud connect used to start a cloud connect engine instance.
    """

    def __init__(self, context, config_file):
        self._context = context
        self._config_file = config_file

    @staticmethod
    def _set_logging(logging):
        _LOGGER.set_level(logging.level)
        stulog.set_log_level(logging.level)

    def run(self):
        """
        Start current client instance to execute each request parsed from config.
        """
        config = load_cloud_connect_config(self._config_file)
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

    def _do_stuff_before_request(self):
        pass

    def _prepare_proxy_setting(self):
        if self._proxy is None:
            return {}
        return {
            'proxy_url': self._proxy.host,
            'proxy_port': self._proxy.port,
            'proxy_username': self._proxy.username,
            'proxy_password': self._proxy.password,
            'proxy_type': self._proxy.type,
            'proxy_rdns': self._proxy.rdns,
        }

    def _invoke_request(self):
        """
        Invoke a request with httplib2 and return it's request.
        :return: A response of request.
        """
        options = self._request.options
        http_conf = self._prepare_proxy_setting()
        if options.auth:
            # FIXME a temp solution
            http_conf['username'] = options.auth.get_username(self._context)
            http_conf['password'] = options.auth.get_password(self._context)
        connection = build_http_connection(http_conf)
        return connection.request(uri=options.url,
                                  method=options.method,
                                  headers=options.header.build(self._context))

    def _is_skip_after_request(self, response):
        """
        Determine if we need to skip the step of after request based on the
        response content.
        :param response: http response of current request
        :return: `True` if don't need process after request else `False`.
        """
        pass

    def _do_stuff_after_request(self, response):
        # FIXME
        pass

    def _update_checkpoint(self, response):
        pass

    def _is_meet_stop_condition(self, response):
        pass

    def start(self):
        """
        Start request instance and exit util meet stop condition.
        """
        self._init_request()

        while 1:
            self._do_stuff_before_request()
            response = self._invoke_request()
            if self._is_skip_after_request(response):
                break
            self._do_stuff_after_request(response)
            if self._is_meet_stop_condition(response):
                break
            self._update_checkpoint(response)

    def _init_request(self):
        request_options = self._request.options
        self._url = request_options.url.render(self._context)
        self._method = request_options.method
