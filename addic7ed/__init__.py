#!/usr/bin/python2

import ConfigParser
import os.path
from urlparse import urljoin
from pyquery import PyQuery as query
import requests
import urllib
import xml.etree.ElementTree as ET

import re

last_url = 'http://www.addic7ed.com/'


class Error(Exception):
    pass


class FatalError(Exception):
    pass


def get(url, raw=False, **params):
    global last_url
    url = urljoin(last_url, url)
    response = requests.get(url, headers={'Referer': last_url}, params=params)
    last_url = response.url
    return response.content if raw else query(response.content)


class Episode(object):

    @classmethod
    def search(cls, query):
        results = get('/search.php', search=query, submit='Search')
        if '/search.php' in last_url:
            return [
                cls(urllib.quote(link.attrib['href'].encode('utf8')), link.text)
                for link in results('.tabel a')
            ]
        else:
            title = results('.titulo').contents()[0].strip()
            return [ cls(last_url, title) ]

    def __init__(self, url, title=None):
        self.url = url
        self.title = title
        self.versions = []

    def __eq__(self, other):
        return self.url == other.url and self.title == other.title

    def __unicode__(self):
        return self.title

    def __repr__(self):
        return 'Episode(%s, %s)' % (repr(self.url), repr(self.title))

    def __str__(self):
        return unicode(self).encode('utf-8')

    def add_version(self, *args):
        self.versions.append(Version(*args))

    def fetch_versions(self):
        if self.versions:
            return

        result = get(self.url)
        tables = result('.tabel95')
        self.title = tables.find('.titulo').contents()[0].strip()

        for i, table in enumerate(tables[2:-1:2]):
            trs = query(table)('tr')

            release = trs.find('.NewsTitle').text().partition(',')[0]
            release = re.sub('version ', '', release, 0, re.I)

            infos = trs.next().find('.newsDate').eq(0).text()
            infos = re.sub('(?:should)? works? with ', '', infos, 0, re.I)

            for tr in trs[2:]:
                tr = query(tr)
                language = tr('.language')
                if not language:
                    continue

                completeness = language.next().text().partition(' ')[0]
                language = language.text()
                download = tr('a[href*=updated]') or tr('a[href*=original]')
                if not download:
                    continue
                hearing_impaired = \
                    bool(tr.next().find('img[title="Hearing Impaired"]'))
                download = download.attr.href
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

    def __unicode__(self):
        return u'{language} - {release} {infos} {completeness} {hi}' \
            .format(hi='HI' if self.hearing_impaired else '',
                    **self.__dict__)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def download(self, filename):
        content = get(self.url, raw=True)

        if content[:9] == '<!DOCTYPE':
            raise FatalError('Daily Download count exceeded.')

        with open(filename, 'wb') as fp:
            fp.write(content)


class UI(object):

    def __init__(self, args, filename):
        self.args = args
        self.filename = filename

    @property
    def batch(self):
        return self.args.batch or self.args.brute_batch

    def select(self, choices):
        if not choices:
            raise Error("Internal error: no choices!")

        if len(choices) == 1 or self.batch:
            result = 1

        else:
            just = len(str(len(choices)))
            index = 1
            for choice in choices:
                print str(index).rjust(just), ':', choice
                index += 1

            while True:
                try:
                    result = int(raw_input('> '))

                except ValueError:
                    result = None

                if result and 1 <= result <= len(choices):
                    break

                else:
                    print "Bad response"

        result = choices[result - 1]
        print result
        return result

    def episode(self, episode, languages=[], releases=[]):
        episode.fetch_versions()
        versions = episode.filter_versions(languages, releases, True,
                                           self.args.hearing_impaired)
        return self.select(versions)

    def confirm(self, question):
        question += ' [yn]> '

        if self.batch:
            return True

        while True:
            answer = raw_input(question)
            if answer in 'yn':
                break

            else:
                print 'Bad answer'

        return answer == 'y'

    def launch(self):
        print '-' * 30
        args = self.args
        filename = self.filename

        if os.path.isfile(filename):
            if filename.endswith('.part'):
                filename = remove_extension(filename)
            if not filename.endswith('.srt'):
                filename = remove_extension(filename) + '.srt'

        print 'Target SRT file:', filename
        ignore = False
        if os.path.isfile(filename):
            print 'File exists.',
            if args.ignore or (not args.overwrite and
                               not self.confirm('Overwrite?')):
                print 'Ignoring.'
                ignore = True

            else:
                print 'Overwriting.'

        if not ignore:
            query, release = file_to_query(filename)

            if args.query:
                query = args.query

            if args.release:
                release = string_set(args.release)

            if args.verbose:
                print 'Using query "{query}" and release "{release}"'.format(
                    release=' '.join(release),
                    query=query
                )

            search_results = Episode.search(query)

            if search_results:
                if self.args.batch and len(search_results) > 1:
                    raise Error('More than one result, aborting')

                episode = self.select(search_results)

                todownload = self.episode(episode, args.language, release)
                todownload.download(filename)

            else:
                print 'No result'

        print


def get_file_alias(filename):

    directory, basename = os.path.split(filename)

    filelist_path = os.path.join(directory, 'filelist')

    if os.path.isfile(filelist_path):
        basename = remove_extension(basename)
        try:
            tree = ET.parse(filelist_path)
        except Exception as e:
            print 'Warning: unable to parse {}: {}'.format(filelist_path, e)
        else:
            for record in tree.findall('.//record'):
                if remove_extension(record.get('to')) == basename:
                    return record.get('from')

    return filename


def file_to_query(filename):
    filename = get_file_alias(filename)
    basename = os.path.basename(filename).lower()
    basename = remove_extension(basename)
    basename = normalize_whitespace(basename)

    # remove parenthesis
    basename = re.sub(r'[\[(].*[\])]', '', basename)

    # remove confusing stopwords
    basename = re.sub(r'\b(?:and|&)\b', '', basename)

    # exceptions
    basename = re.sub(r'\bdont\b', 'don\'t', basename)
    basename = re.sub(r'\bcsi new york\b', 'csi ny', basename)

    episode = re.search(r'season\s+0*(\d+)\s+episode\s+(\d+)', basename, re.I) or \
        re.search(r'\S*?0*(\d+)[xe](\d+)', basename) or \
        re.search(r'()(\d+)', basename)

    if episode:
        index = basename.find(episode.group(0))
        release = basename[index + len(episode.group(0)):]
        basename = basename[:index]
        season = episode.group(1)
        number = episode.group(2)

        if not season and len(number) >= 3:
            season = number[1]
            number = number[1:]

        if season:
            episode = 'x'.join((season, number))
        else:
            episode = number

    else:
        episode = ''
        release = basename

    query = normalize_whitespace(' '.join((basename, episode)))
    release = normalize_release(string_set(release))
    return query, release


def normalize_release(release):
    equivalences = (
        set(('lol', 'sys', 'dimension')),
        set(('xii', 'asap', 'immerse')),
    )

    remove = set(('hdtv', 'x264', '720p'))

    release -= remove

    for equivalence in equivalences:
        if release & equivalence:
            release |= equivalence

    return release


def remove_extension(filename):
    return filename.rpartition('.')[0] if '.' in filename else filename


def normalize_whitespace(string):
    # change extra characters to space
    return re.sub(r'[\s._,-]+', ' ', string).strip()


def string_set(string):
    string = normalize_whitespace(string.lower())
    return set(string.split(' ')) if string else set()


class Arguments(object):
    def __init__(self):
        self.language = []
        self.default_language = []
        self.verbose = False
        self.hearing_impaired = False
        self.batch = False
        self.brute_batch = False
        self.query = None
        self.release = None
        self.overwrite = False
        self.ignore = False

    @staticmethod
    def get_paths():
        # Linux and OSX:
        paths = [
            os.path.join(os.path.expanduser('~'), '.config', 'addic7ed'),
            os.path.join(os.path.expanduser('~'), '.addic7ed'),
        ]

        # Windows
        if 'APPDATA' in os.environ:
            paths.append(os.path.join(os.environ['APPDATA'], 'config'))

        return paths

    def read_defaults(self):
        paths = self.get_paths()
        valid_paths = (path for path in paths if os.path.isfile(path))
        configuration_path = next(valid_paths, None)

        self.default_language = []

        if configuration_path is not None:
            config = ConfigParser.ConfigParser(allow_no_value=True)
            config.read(configuration_path)

            if config.has_section('flags'):
                self._read_flags(config)

            if config.has_section('languages'):
                self._read_languages(config)

    def _read_flags(self, config):
        def getbool(name, default=False):
            if not config.has_option('flags', name):
                return default

            value = config.get('flags', name)
            if isinstance(value, basestring):
                return config.getboolean('flags', name)

            return value is None

        self.verbose = getbool('verbose')
        self.hearing_impaired = getbool('hearing-impaired')
        self.batch = getbool('batch')
        self.brute_batch = getbool('brute-batch')
        self.overwrite = getbool('overwrite')
        self.ignore = getbool('ignore')

    def _read_languages(self, config):
        self.default_language = [l for l, v in config.items('languages')
                                 if v is not False]

    def finalize(self):
        if not self.language:
            self.language = self.default_language[:]


def main():

    import argparse
    import textwrap
    import pkg_resources
    version = pkg_resources.require('addic7ed')[0].version

    epilog = '''
    Configuration file:

      You can store frequently used options in a configuration file. Create a
      file at ~/.config/addic7ed (Linux, OSX) or %APPDATA%/config (Windows),
      and it will be parsed using the Python ConfigParser (see example below).
      It can contain two sections:

      * [flags], to set a flag (verbose, hearing-impaired, overwrite, ignore,
        batch or brute-batch)

      * [languages], to list prefered languages

      Example:

        [flags]
        hearing-impaired = no
        batch

        [languages]
        french
        english

    Video organizer:
      video-organizer format is supported. If a "filelist" file is next to an
      episode, it will use it to extract its real name and forge the good
      query. See https://github.com/JoelSjogren/video-organizer for further
      informations.
    '''

    parser = argparse.ArgumentParser(
        description='Downloads SRT files from addic7ed.com.',
        epilog=textwrap.dedent(epilog),
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('file', nargs='+',
                        help='Video file name.')

    parser.add_argument('-V', '--version', action='version',
                        version='%%(prog)s version %s' % version)

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print some debugging informations.')

    custom = parser.add_argument_group('Query customization')
    custom.add_argument('-q', '--query',
                        help='Custom query. (default: based on the filename)')

    custom.add_argument('-r', '--release',
                        help='Custom release. (default: based on the '
                        'filename)')

    custom.add_argument('-l', '--language', action='append', default=[],
                        help='Prefer a language. (could be specified more '
                        'than one time for fallbacks)')

    custom.add_argument('-H', '--hearing-impaired', action='store_true',
                        help='Prefer hearing impaired version.')

    custom.add_argument('--no-hearing-impaired', dest='hearing_impaired',
                        action='store_false')

    batch = parser.add_argument_group('Automation')
    batch.add_argument('-o', '--overwrite', action='store_true',
                       help='Always overwrite the SRT if it exists.')

    batch.add_argument('-i', '--ignore', action='store_true',
                       help='Never overwrite the SRT if it exists.')

    batch.add_argument('-b', '--batch', action='store_true',
                       help='Do not ask anything, get the best matching '
                       'subtitle. Cancel if the search returns more than one '
                       'result.')

    batch.add_argument('-bb', '--brute-batch', action='store_true',
                       help='Do not ask anything, get the best matching '
                       'subtitle. Use the first result of the search.')

    args = Arguments()
    args.read_defaults()

    parser.parse_args(namespace=args)

    args.finalize()

    try:
        for file in args.file:
            try:
                UI(args, file).launch()
            except Error as e:
                print 'Error:', e

    except FatalError as e:
        print 'Fatal error:', e
        exit(1)

    except KeyboardInterrupt:
        print 'Aborted by user'
        exit(1)


if __name__ == '__main__':
    main()
