
from pyquery import PyQuery as query
import re
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from addic7ed.request import session
from addic7ed.version import Version
from addic7ed.compat import encode

__all__ = ['search', 'Episode']


class Episode(object):

    def __init__(self, url, title=None):
        self.url = url
        self.title = title
        self.versions = []

    def __eq__(self, other):
        return self.url == other.url and self.title == other.title

    def __repr__(self):
        return 'Episode(%s, %s)' % (repr(self.url), repr(self.title))

    def __str__(self):
        return self.title

    def add_version(self, *args):
        self.versions.append(Version(*args))

    def fetch_versions(self):
        if self.versions:
            return

        result = session.get(self.url)
        tables = result('.tabel95')
        self.title = tables.find('.titulo').contents()[0].strip()

        for i, table in enumerate(tables[2:-1:2]):
            trs = query(table)('tr')

            release = encode(trs.find('.NewsTitle').text().partition(',')[0])
            release = re.sub('version ', '', release, 0, re.I)

            infos = encode(trs.next().find('.newsDate').eq(0).text())
            infos = re.sub('(?:should)? works? with ', '', infos, 0, re.I)

            for tr in trs[2:]:
                tr = query(tr)
                language = tr('.language')
                if not language:
                    continue

                completeness = encode(language.next().text().partition(' ')[0])
                language = encode(language.text())
                download = tr('a[href*=updated]') or tr('a[href*=original]')
                if not download:
                    continue
                hearing_impaired = \
                    bool(tr.next().find('img[title="Hearing Impaired"]'))
                download = encode(download.attr.href)
                self.add_version(download, language, release, infos,
                                 completeness, hearing_impaired)

    def filter_versions(self, languages=[], release=set(), completed=True,
                        hearing_impaired=False):

        for version in self.versions:
            version.weight = 0
            version.match_languages(languages)
            version.match_release(release)
            version.match_completeness(completed)
            version.match_hearing_impaired(hearing_impaired)

        result = []
        last_weight = None
        for version in sorted(self.versions, key=lambda v: v.weight,
                              reverse=True):
            if last_weight is None:
                last_weight = version.weight
            elif last_weight - version.weight >= 0.5:
                break

            result.append(version)

        return result


def search(query):
    results = session.get('/search.php',
                          params={'search': query, 'submit': 'Search'})
    last_url = session.last_url
    if '/search.php' in last_url:
        return [
            Episode(quote(encode(link.attrib['href'])),
                    encode(link.text))
            for link in results('.tabel a')
        ]
    else:
        title = encode(results('.titulo').contents()[0]).strip()
        return [Episode(last_url, title)]
