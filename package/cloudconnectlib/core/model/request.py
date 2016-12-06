from ..exception import ConfigException
from ..template import compile_template


class Request(object):
    def __init__(self, options, before_request, skip_after_request,
                 after_request, checkpoint, loop_mode):
        self._options = options
        self._before_request = before_request
        self._skip_after_request = skip_after_request
        self._after_request = after_request
        self._checkpoint = checkpoint
        self._loop_mode = loop_mode

    @property
    def options(self):
        return self._options

    @property
    def before_request(self):
        return self._before_request

    @property
    def skip_after_request(self):
        return self._skip_after_request

    @property
    def after_request(self):
        return self._after_request

    @property
    def checkpoint(self):
        return self._checkpoint

    @property
    def loop_mode(self):
        return self._loop_mode


class BasicAuthorization(object):
    def __init__(self, options):
        if not options:
            raise ConfigException("the options field of auth is empty")
        self._username = options.get("username")
        self._password = options.get("password")
        if not self._username:
            raise ConfigException("username of auth is empty")
        if not self._password:
            raise ConfigException("password of auth is empty")
        self._username = compile_template(self._username)
        self._password = compile_template(self._password)

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self.password


class Options(object):
    def __init__(self, url, header=None, method="GET", auth=None):
        self._header = header
        self._url = compile_template(url)
        self._method = method.upper()
        self._auth = auth

    @property
    def header(self):
        return self._header

    @property
    def url(self):
        return self._url

    @property
    def method(self):
        return self._method
