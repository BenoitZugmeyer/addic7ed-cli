#!/usr/bin/python2

import os.path
from urlparse import urljoin
from pyquery import PyQuery as query
import requests

import re

last_url = 'http://www.addic7ed.com/'


class Error(Exception):
    pass


class FatalError(Exception):
    pass


def get(url, raw=False, **params):
    global last_url
    url = urljoin(last_url, url)
    request = requests.get(url, headers={'Referer': last_url}, params=params)
    last_url = url
    return request.content if raw else query(request.content)


class Episode(object):

    @classmethod
    def search(cls, query):
        links = get('/search.php', search=query, submit='Search')('.tabel a')
        return [cls(link.attrib['href'], link.text) for link in links]

    def __init__(self, url, title=None):
        self.url = url
        self.title = title
        self.versions = []

    def __eq__(self, other):
        return self.url == other.url and self.title == other.title

    def __unicode__(self):
        return self.title

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
        release = complete_release(release)
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
        self.release_hash = complete_release(string_set(infos) |
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

        if os.path.isfile(filename) and not filename.endswith('.srt'):
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
                release = string_set(' '.join(args.release))

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


def file_to_query(filename):
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

    episode = re.search(r'\S*?0*(\d+)[xe](\d+)', basename) or \
        re.search(r'(\d+)', basename)

    if episode:
        index = basename.find(episode.group(0))
        release = basename[index + len(episode.group(0)):]
        basename = basename[:index]
        episode = 'x'.join(episode.groups())

    else:
        episode = ''
        release = basename

    query = normalize_whitespace(' '.join((basename, episode)))
    release = string_set(release)
    return query, release


def complete_release(release):
    equivalences = (
        set(('lol', 'sys', 'dimension')),
        set(('xii', 'asap', 'immerse')),
    )

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


def main():

    import argparse
    parser = argparse.ArgumentParser(description='Downloads SRT files from '
                                     'addic7ed.com.')

    parser.add_argument('file', nargs='+',
                        help='Video file name.')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print some debugging informations.')

    custom = parser.add_argument_group('Query customization')
    custom.add_argument('-q', '--query',
                        help='Custom query. (default: based on the filename)')

    custom.add_argument('-r', '--release', action='append', default=[],
                        help='Custom release. (default: based on the '
                        'filename)')

    custom.add_argument('-l', '--language', action='append', default=[],
                        help='Prefer a language. (could be specified more '
                        'than one time for fallbacks)')

    custom.add_argument('-H', '--hearing-impaired', action='store_true',
                        help='Prefer hearing impaired version.')

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

    args = parser.parse_args()

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
