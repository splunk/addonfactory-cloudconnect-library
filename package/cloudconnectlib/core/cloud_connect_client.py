from ..configuration.loaders import load_cloud_connect_config
from ..splunktaucclib.common import log as stulog


class CloudConnectClient(object):
    """
    The client of cloud connect used to start a cloud connect engine instance.
    """

    def __init__(self, context, config_file):
        self._context = context
        self._config_file = config_file

    def run(self):
        """
        Start current client instance to execute each request parsed from config.
        """
        config = load_cloud_connect_config(self._config_file)
        stulog.set_log_level(config.global_settings.logging.level)

        for item in config.requests:
            request = CloudConnectRequest(request=item,
                                          context=self._context,
                                          proxy=config.global_settings.proxy)
            request.start()


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

    def _is_skip_after_request(self, response):
        pass

    def _prepare_before_request(self):
        pass

    def _invoke_request(self):
        # FIXME send request
        return {}

    def _do_after_request(self, response):
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
            self._prepare_before_request()
            response = self._invoke_request()
            if self._is_skip_after_request(response):
                break
            self._do_after_request(response)
            if self._is_meet_stop_condition(response):
                break
            self._update_checkpoint(response)

    def _init_request(self):
        request_options = self._request.options
        self._url = request_options.url.render(self._context)
        self._method = request_options.method

    def _before_request(self):
        pass
