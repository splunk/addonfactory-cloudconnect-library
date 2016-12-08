import json
import logging
import urllib
import urlparse

from httplib2 import ProxyInfo, Http, socks
from .exceptions import HTTPError

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging


class HTTPResponse(object):
    """
    HTTPResponse class wraps response of HTTP request for later use.
    """

    def __init__(self, header, body):
        self._status_code = header.status
        self._header = header
        self._body = body

    @property
    def header(self):
        return self._header

    @property
    def body(self):
        """
        Return response body as a `string`.
        :return: A `string`
        """
        return self._body

    @property
    def status_code(self):
        """
        Return response status code.
        :return: A `integer`
        """
        return self._status_code


class HTTPRequest(object):
    """
    HTTPRequest class represents a single request to send HTTP request until
    reached it's stop condition.
    """

    _PROXY_TYPE = {
        'http': socks.PROXY_TYPE_HTTP,
        'http_no_tunnel': socks.PROXY_TYPE_HTTP_NO_TUNNEL,
        'socks4': socks.PROXY_TYPE_SOCKS4,
        'socks5': socks.PROXY_TYPE_SOCKS5,
    }

    def __init__(self, proxy=None):
        """
        Constructs a `HTTPRequest` with a optional proxy setting.
        :param proxy: A optional `Proxy` object contains proxy related
         settings.
        """
        self._proxy = proxy
        self._connection = None

    @staticmethod
    def _encode_url(url):
        if not url:
            raise ValueError('request url unexpected to be empty')
        parts = url.split('?', 1)
        if len(parts) == 1:
            return url
        params = urlparse.parse_qs(parts[1])
        return '?'.join([parts[0], urllib.urlencode(params, True)])

    def request(self, url, method='GET', header=None, body=None):
        """
        Invoke a request with httplib2 and return it's response.
        :param url: url address to send request to.
        :param method: request method `GET` by default.
        :param header: request header.
        :param body: request body.
        :return: A `HTTPResponse` object.
        """
        if self._connection is None:
            self._connection = self._build_http_connection(self._proxy)

        uri = self._encode_url(url) if method == 'GET' else url

        _LOGGER.info('Preparing to invoke request to [%s]', uri)

        rob = json.dumps(body) if body else None
        response, content = self._connection.request(
            uri, body=rob, method=method, headers=header
        )

        if response.status not in (200, 201):
            raise HTTPError(response=response, status=response.status)

        return HTTPResponse(response, content)

    def _prepare_proxy_info(self, proxy):
        if not proxy or not proxy.enabled:
            _LOGGER.debug('Proxy not enabled')
            return None

        username = proxy.username if 'username' in proxy else None
        password = proxy.password if 'password' in proxy else None
        proxy_type = self._PROXY_TYPE.get(proxy.type) or self._PROXY_TYPE['http']

        return ProxyInfo(proxy_host=proxy.host,
                         proxy_port=int(proxy.port),
                         proxy_type=proxy_type,
                         proxy_user=username,
                         proxy_pass=password,
                         proxy_rdns=proxy.rdns)

    def _build_http_connection(self, proxy=None,
                               timeout=120,
                               disable_ssl_cert_validation=True):
        return Http(proxy_info=self._prepare_proxy_info(proxy),
                    timeout=timeout,
                    disable_ssl_certificate_validation=disable_ssl_cert_validation)
