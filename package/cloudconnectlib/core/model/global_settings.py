import logging

from .. import util


class Logging(object):
    _logging_level = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARN': logging.WARN,
        'ERROR': logging.ERROR,
        'FATAL': logging.FATAL,
    }

    def __init__(self, level='INFO'):
        self._level = self._logging_level.get(level, logging.INFO)

    @property
    def level(self):
        return self._level


class Proxy(object):
    """
    A entity class to hold proxy related setting.
    """
    _allowed_proxy_types = ['http', 'http_no_tunnel', 'socks4', 'socks5']

    def __init__(self, enabled=False, host=None, port=None, username=None,
                 password=None, type=None, rdns=None):
        self._enabled = util.is_true(enabled)
        self._host = host
        self._port = int(port)
        self._username = username
        self._password = password
        self._type = type if type in self._allowed_proxy_types else 'http'
        self._rdns = util.is_true(rdns)

    @property
    def enabled(self):
        return self._enabled

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def type(self):
        return self._type

    @property
    def rdns(self):
        return self._rdns


class GlobalSetting(object):
    def __init__(self, proxy=None, logging=None):
        self._proxy = proxy
        self._logging = logging

    @property
    def proxy(self):
        return self._proxy

    @property
    def logging(self):
        return self._logging
