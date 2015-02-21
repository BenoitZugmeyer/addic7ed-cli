
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests
from pyquery import PyQuery

__all__ = ['session']


class Response(object):

    def __init__(self, response):
        self._response = response
        self._query = None

    def __getattr__(self, name):
        return getattr(self._response, name)

    def __call__(self, query):
        if not self._query:
            self._query = PyQuery(self.content)

        return self._query(query)


class Session(requests.Session):

    last_url = 'http://www.addic7ed.com/'

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.last_url, url)
        self.headers = {'Referer': self.last_url}
        response = super(Session, self).request(method, url, *args, **kwargs)
        self.last_url = response.url
        return Response(response)


session = Session()
