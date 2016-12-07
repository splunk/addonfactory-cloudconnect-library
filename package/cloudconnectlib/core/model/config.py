class CloudConnectConfigV1(object):
    """
    CloudConnectConfigV1 class holds all configs loaded from JSON file
    passed from user.
    """

    def __init__(self, meta, parameters, global_settings, requests):
        self._meta = meta
        self._parameters = parameters
        self._global_settings = global_settings
        self._requests = requests

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
