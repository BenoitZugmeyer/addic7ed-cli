import os

from addic7ed.error import Error
from addic7ed.util import remove_extension, file_to_query, string_set
from addic7ed.episode import search


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
        filename = remove_extension(self.filename) + '.srt'

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

            search_results = search(query)

            if search_results:
                if self.args.batch and len(search_results) > 1:
                    raise Error('More than one result, aborting')

                episode = self.select(search_results)

                todownload = self.episode(episode, args.language, release)
                todownload.download(filename)

            else:
                print 'No result'

        print
