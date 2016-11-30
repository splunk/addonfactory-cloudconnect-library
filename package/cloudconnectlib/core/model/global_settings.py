from .. import util
from httplib2 import socks
import logging


class Logging(object):
    def __init__(self, level="INFO"):
        level = level.upper()
        if level == "DEBUG":
            self._level = logging.DEBUG
        elif level == "INFO":
            self._level = logging.INFO
        elif level == "WARN":
            self._level = logging.WARN
        elif level == "ERROR":
            self._level = logging.ERROR
        else:
            self._level = logging.INFO

    @property
    def level(self):
        return self._level


class Proxy(object):
    """
    A entity class to hold proxy related setting.
    """

    proxy_type_to_code = {
        "http": socks.PROXY_TYPE_HTTP,
        "http_no_tunnel": socks.PROXY_TYPE_HTTP_NO_TUNNEL,
        "socks4": socks.PROXY_TYPE_SOCKS4,
        "socks5": socks.PROXY_TYPE_SOCKS5,
    }

    def __init__(self, enabled=False, host=None, port=None, username=None,
                 password=None, type=None, rdns=None):
        self._enabled = util.is_true(enabled)
        self._host = host
        self._port = int(port)
        self._username = username
        self._password = password
        if type in Proxy.proxy_type_to_code:
            self._type = type
        else:
            self._type = socks.PROXY_TYPE_HTTP
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
