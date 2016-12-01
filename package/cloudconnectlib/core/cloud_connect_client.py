from .model.config import CloudConnectConfig as config
from ..splunktaucclib.common import log as stulog


class CloudConnectClient(object):
    def __init__(self, context, cc_config):
        self._context = context
        self._config = cc_config

    def run(self):
        stulog.set_log_level(self._config.global_settings.logging.level)
        for request in self._config.requests:
            CloudConnectRequest(request,self._context,
                                self._config.global_settings.proxy).run()


class CloudConnectRequest(object):
    def __init__(self, request, context, proxy=None):
        self._request = request
        self._context = context
        self._proxy = proxy

    def run(self):
        return

    def init_request(self):
        request_options = self._request.options
        self._url = request_options.url.render(self._context)
        self._method = request_options.method
        


    def before_request_handle

