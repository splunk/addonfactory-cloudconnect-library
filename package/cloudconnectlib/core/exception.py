class ConfigException(Exception):
    """
    Config exception
    """
    pass


class HTTPError(Exception):
    """
    HTTPError raised when HTTP request returned a error.
    """

    def __init__(self, response):
        self.status = response.status
        self.response = response
