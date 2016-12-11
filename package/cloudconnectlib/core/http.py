import os
import traceback
import urllib
import urlparse

from cloudconnectlib.common.util import register_module
from . import defaults
from .exceptions import HTTPError

register_module(os.path.join(os.path.dirname(__file__), 'cacerts'))

from httplib2 import ProxyInfo, Http, socks, SSLHandshakeError

from ..common import log as _logger



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
        self._proxy_info = self._prepare_proxy_info(proxy)
        self._connection = None

    @staticmethod
    def _encode_url(url):
        if not url:
            raise ValueError('Request url unexpected to be empty')
        parts = url.split('?', 1)
        if len(parts) == 1:
            return url
        params = urlparse.parse_qs(parts[1])
        return '?'.join([parts[0], urllib.urlencode(params, True)])

    def _send_request(self, uri, method, headers=None, body=None):
        if self._connection is None:
            self._connection = self._build_http_connection(
                proxy_info=self._proxy_info,
                disable_ssl_cert_validation=False)

        try:
            return self._connection.request(
                uri, body=body, method=method, headers=headers)
        except SSLHandshakeError:
            _logger.warn(
                "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verification failed. "
                "The certificate of the https server [%s] is not trusted, "
                "this add-on will proceed to connect with this certificate. "
                "You may need to check the certificate and "
                "refer to the documentation and add it to the trust list. %s",
                uri,
                traceback.format_exc()
            )

            self._connection = self._build_http_connection(
                proxy_info=self._proxy_info,
                disable_ssl_cert_validation=True)
            return self._connection.request(
                uri, body=body, method=method, headers=headers)

    def request(self, url, method='GET', headers=None, body=None):
        """
        Invoke a request with httplib2 and return it's response.
        :param url: url address to send request to.
        :param method: request method `GET` by default.
        :param headers: request headers.
        :param body: request body.
        :return: A `HTTPResponse` object.
        """

        if body and not isinstance(body, str):
            raise TypeError('Request body type must be str')

        if self._connection is None:
            self._connection = self._build_http_connection(self._proxy_info)

        uri = self._encode_url(url) if method.strip().upper() == 'GET' else url

        _logger.info('Preparing to invoke request to [%s]', uri)

        response, content = self._connection.request(
            uri, body=body, method=method, headers=headers
        )

        if response.status not in (200, 201):
            raise HTTPError(response=response, status=response.status)

        return HTTPResponse(response, content)

    def _prepare_proxy_info(self, proxy):
        if not proxy or not proxy.enabled:
            _logger.debug('Proxy is not enabled')
            return None

        username = proxy.username \
            if 'username' in proxy and proxy.username else None
        password = proxy.password \
            if 'password' in proxy and proxy.password else None

        proxy_type = self._PROXY_TYPE.get(proxy.type) or self._PROXY_TYPE['http']

        return ProxyInfo(proxy_host=proxy.host,
                         proxy_port=int(proxy.port),
                         proxy_type=proxy_type,
                         proxy_user=username,
                         proxy_pass=password,
                         proxy_rdns=proxy.rdns)

    @staticmethod
    def _build_http_connection(
            proxy_info=None,
            timeout=defaults.timeout,
            disable_ssl_cert_validation=defaults.disable_ssl_cert_validation):
        return Http(proxy_info=proxy_info,
                    timeout=timeout,
                    disable_ssl_certificate_validation=disable_ssl_cert_validation)
