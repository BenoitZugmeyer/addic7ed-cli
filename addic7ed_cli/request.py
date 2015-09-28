
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests
from pyquery import PyQuery
from addic7ed_cli.error import Error

__all__ = ['session']


class Response(object):

    def __init__(self, response):
        self._response = response
        self._query = None

    def __getattr__(self, name):
        return getattr(self._response, name)

    def __call__(self, query):
        if self.status_code >= 300:
            raise Error("HTTP request to '{}' has failed with status {}"
                        .format(self.url, self.status_code))

        if not self._query:
            self._query = PyQuery(self.content)

        return self._query(query)


class Session(requests.Session):

    last_url = 'http://www.addic7ed.com/'

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.last_url, url)
        self.headers = {
            'Referer': self.last_url,

            # Don't use Keep-Alive requests as requests/urllib3 currently has a bug
            # https://github.com/kennethreitz/requests/issues/2568
            'Connection': 'close',

            # Without any user agent, addic7ed.com sometimes returns a 304 status code
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36',
        }
        response = super(Session, self).request(method, url, *args, **kwargs)
        self.last_url = response.url
        return Response(response)


session = Session()
