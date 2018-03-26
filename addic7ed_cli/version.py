
import re
import zipfile
import io
import shutil

from addic7ed_cli.util import parse_release
from addic7ed_cli.error import FatalError
from addic7ed_cli.request import session
from addic7ed_cli.language import iso639_3_codes


class Version(object):
    def __init__(self, id, language_id, version, url, language, release, infos,
                 completeness, hearing_impaired):
        self.id = id
        self.language_id = language_id
        self.version = version
        self.url = url
        self.language = language
        self.release = release
        self.infos = infos
        self.completeness = completeness
        self.release_hash = parse_release(infos) | parse_release(release)
        self.hearing_impaired = hearing_impaired
        self.weight = 0

    @property
    def iso639_language(self):
        return iso639_3_codes[self.language]

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

    @staticmethod
    def multidownload(files):
        data = [
            ('multishow[]',
             '{0.language_id}/{0.id}/{0.version}'.format(version))
            for (version, _) in files
        ]

        result = session.post('/downloadmultiple.php', data=data)

        z = zipfile.ZipFile(io.BytesIO(result.content))
        zipfilenames = (n for n in z.namelist() if n.endswith('.srt'))

        for (filename, zipfilename) in zip((filename for (_, filename) in files), zipfilenames):
            with open(filename, 'wb') as output:
                shutil.copyfileobj(z.open(zipfilename), output)
