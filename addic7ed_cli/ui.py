
import os
from getpass import getpass

from addic7ed_cli.error import Error
from addic7ed_cli.util import remove_extension, file_to_query, string_set
from addic7ed_cli.episode import search
from addic7ed_cli.compat import echo, input
from addic7ed_cli.login import login


class UI(object):

    def __init__(self, args):
        self.args = args

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
                echo(str(index).rjust(just), ':', choice)
                index += 1

            while True:
                answer = input('[1] > ')
                if not answer:
                    result = 1

                else:
                    try:
                        result = int(answer)

                    except ValueError:
                        result = None

                if result and 1 <= result <= len(choices):
                    break

                else:
                    echo("Bad response")

        result = choices[result - 1]
        echo(result)
        return result

    def confirm(self, question, default=None):
        responses = 'yn' if default is None else 'Yn' if default else 'yN'
        question += ' [{}] > '.format(responses)

        if self.batch:
            return True

        while True:
            answer = input(question).lower()
            if answer in ('y', 'n'):
                return answer == 'y'

            elif answer == '' and default is not None:
                return default

            else:
                echo('Bad answer')


class SearchUI(UI):

    def episode(self, episode, languages=[], releases=[]):
        episode.fetch_versions()
        versions = episode.filter_versions(languages, releases, True,
                                           self.args.hearing_impaired)
        return self.select(versions)

    def launch_file(self, filename):
        echo('-' * 30)
        args = self.args
        filename = remove_extension(filename) + '.srt'

        echo('Target SRT file:', filename)
        ignore = False
        if os.path.isfile(filename):
            echo('File exists.', end=' ')
            if args.ignore or (not args.overwrite and
                               not self.confirm('Overwrite?', True)):
                echo('Ignoring.')
                ignore = True

            else:
                echo('Overwriting.')

        if not ignore:
            query, release = file_to_query(filename)

            if args.query:
                query = args.query

            if args.release:
                release = string_set(args.release)

            if args.verbose:
                echo('Using query "{query}" and release "{release}"'.format(
                    release=' '.join(release),
                    query=query
                ))

            search_results = search(query)

            if search_results:
                if self.args.batch and len(search_results) > 1:
                    raise Error('More than one result, aborting')

                episode = self.select(search_results)

                todownload = self.episode(episode, args.language, release)
                todownload.download(filename)

            else:
                echo('No result')

        echo()

    def launch(self):
        for file in self.args.file:
            try:
                self.launch_file(file)
            except Error as e:
                echo('Error:', e)


class LoginUI(UI):

    def launch(self):
        user = input('User: ')
        password = getpass('Password: ')

        self.args.session = login(user, password)
        self.args.save_session()


class LogoutUI(UI):

    def launch(self):
        self.args.session = None
        self.args.save_session()
        echo('Logged out')
