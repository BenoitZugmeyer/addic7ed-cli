
import os
from getpass import getpass

from addic7ed_cli.error import Error
from addic7ed_cli.util import remove_extension, file_to_query, string_set
from addic7ed_cli.episode import search
from addic7ed_cli.compat import echo, input
from addic7ed_cli.login import login, get_current_user
from addic7ed_cli.version import Version


class UI(object):

    def __init__(self, args):
        self.args = args

    @property
    def batch(self):
        return self.args.batch or self.args.brute_batch

    def select(self, choices):
        if not choices:
            raise Error("Internal error: no choices!")

        chosen_index = None
        skipping = False

        if len(choices) == 1 or self.batch:
            chosen_index = 1

        else:
            just = len(str(len(choices)))
            index = 1
            for choice in choices:
                echo(" {} : {}".format(str(index).rjust(just), choice))
                index += 1

            echo(" S : Skip")

            while True:
                answer = input('[1] > ')

                if not answer:
                    chosen_index = 1

                elif answer.lower() == "s":
                    skipping = True

                else:
                    try:
                        chosen_index = int(answer)

                    except ValueError:
                        pass

                if skipping or (chosen_index and
                                1 <= chosen_index <= len(choices)):
                    break

                else:
                    echo("Bad response")

        if skipping:
            echo("Skipping")
            return None

        result = choices[chosen_index - 1]
        echo("{}".format(result))
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

    def should_ignore_file(self, filename):
        ignore = False
        echo('Target SRT file: {}'.format(filename))
        if os.path.isfile(filename):
            if self.args.ignore or (not self.args.overwrite and
                                    not self.confirm('Overwrite?', True)):
                echo('File exists. Ignoring.')
                ignore = True

            else:
                echo('File exists. Overwriting.')

        return ignore

    def launch_file(self, filename):
        args = self.args

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

        if not search_results:
            echo('No result')
            return

        if self.args.batch and len(search_results) > 1:
            raise Error('More than one result, aborting')

        episode = self.select(search_results)

        return episode and self.episode(episode, args.language, release)

    def iter_files(self):
        for file_arg in self.args.file:
            try:

                if not self.args.lang_suffix:
                    output_file = remove_extension(file_arg) + '.srt'
                    if self.should_ignore_file(output_file):
                        continue

                version = self.launch_file(file_arg)
                if version:
                    if self.args.lang_suffix:
                        output_file = "{}.{}.srt".format(
                            remove_extension(file_arg),
                            version.iso639_language,
                        )
                        if self.should_ignore_file(output_file):
                            continue

                    yield version, output_file
                echo()

            except Error as e:
                echo('Error: {}'.format(e))

    def launch(self):
        use_multidownload = bool(get_current_user()) and \
            len(self.args.file) > 1

        files = list(self.iter_files())

        if not files:
            echo('Nothing to download')

        elif use_multidownload:
            echo('Using multi-download')
            Version.multidownload(files)

        else:
            for (version, output_file) in files:
                version.download(output_file)


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
