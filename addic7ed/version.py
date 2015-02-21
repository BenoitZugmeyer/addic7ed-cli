
import re

from addic7ed.util import string_set, normalize_release
from addic7ed.error import FatalError
from addic7ed.request import session


class Version(object):
    def __init__(self, url, language, release, infos, completeness,
                 hearing_impaired):
        self.url = url
        self.language = language
        self.release = release
        self.infos = infos
        self.completeness = completeness
        self.release_hash = normalize_release(string_set(infos) |
                                              string_set(release))
        self.hearing_impaired = hearing_impaired
        self.weight = 0

    def __eq__(self, other):
        return self.url == other.url and self.language == other.language

    def match_languages(self, languages):
        if not languages:
            return

        l = float(len(languages))
        weight = 0
        for index, language in enumerate(languages):
            if language.lower() in self.language.lower():
                weight += (l - index) / l

        self.weight += weight

    def match_release(self, release):
        if not release:
            return

        self.weight += len(release & self.release_hash) / float(len(release))

    def match_completeness(self, completeness):
        match = re.match('(\d+\.?\d+)', self.completeness)
        weight = float(match.group(1)) / 100 if match else 1
        self.weight += weight

    def match_hearing_impaired(self, hearing_impaired):
        if hearing_impaired == self.hearing_impaired:
            self.weight += 0.1

    def __str__(self):
        return '{language} - {release} {infos} {completeness} {hi}' \
            .format(hi='HI' if self.hearing_impaired else '',
                    **self.__dict__)

    def download(self, filename):
        content = session.get(self.url).content

        if content[:9] == '<!DOCTYPE':
            raise FatalError('Daily Download count exceeded.')

        with open(filename, 'wb') as fp:
            fp.write(content)
