class CloudConnectConfigV1(object):
    """
    A entity class to hold all configs loaded from JSON file.
    """

    def __init__(self, meta, parameters, global_settings, requests=None):
        self._meta = meta
        self._parameters = parameters
        self._global_settings = global_settings
        self._requests = requests or []

    def add_request(self, request):
        self._requests.append(request)

    @property
    def meta(self):
        return self._meta

    @property
    def global_settings(self):
        return self._global_settings

    @property
    def requests(self):
        return self._requests

    @property
    def parameters(self):
        return self._parameters
