import json
import logging
import urllib
import urlparse

from httplib2 import ProxyInfo, Http
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

    def __init__(self, proxy=None):
        """
        Constructs a `HTTPRequest` with a optional proxy setting.
        :param proxy: A optional `Proxy` object contains proxy related
         settings.
        """
        self._proxy = proxy
        self._http = None

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
        if self._http is None:
            self._http = self._build_http_connection(self._proxy)

        uri = self._encode_url(url) if method == 'GET' else url

        _LOGGER.info('Preparing to invoke request to [%s]', uri)

        rob = json.dumps(body) if body else None
        response, content = self._http.request(uri, body=rob, method=method, headers=header)

        if response.status not in (200, 201):
            raise HTTPError(response=response, status=response.status)

        return HTTPResponse(response, content)

    @staticmethod
    def _build_http_connection(proxy=None,
                               timeout=120,
                               disable_ssl_cert_validation=True):
        if proxy and proxy.enabled:
            proxy_info = ProxyInfo(proxy_type=proxy.type,
                                   proxy_host=proxy.host,
                                   proxy_port=proxy.port,
                                   proxy_user=proxy.username,
                                   proxy_pass=proxy.password,
                                   proxy_rdns=proxy.rdns)
            http = Http(proxy_info=proxy_info,
                        timeout=timeout,
                        disable_ssl_certificate_validation=disable_ssl_cert_validation)
        else:
            http = Http(timeout=timeout,
                        disable_ssl_certificate_validation=disable_ssl_cert_validation)
        return http
