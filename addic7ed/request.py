
from pyquery import PyQuery as query
from urlparse import urljoin
import requests


last_url = 'http://www.addic7ed.com/'

__all__ = ['get', 'get_last_url']


def get(url, raw=False, **params):
    global last_url
    url = urljoin(last_url, url)
    response = requests.get(url, headers={'Referer': last_url}, params=params)
    last_url = response.url
    return response.content if raw else query(response.content)


def get_last_url():
    return last_url
