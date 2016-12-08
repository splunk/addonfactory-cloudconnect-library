class ConfigException(Exception):
    """
    Config exception
    """
    pass


class HTTPError(Exception):
    """
    HTTPError raised when HTTP request returned a error.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize HTTPError with `response` object and `status`.
        """
        self.response = kwargs.pop('response', None)
        self.status = kwargs.pop('status', None)
        super(HTTPError, self).__init__(*args, **kwargs)
