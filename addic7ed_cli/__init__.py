#!/usr/bin/python2

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import os.path
import argparse

from addic7ed_cli.compat import echo, basestring
from addic7ed_cli.ui import SearchUI, LoginUI, LogoutUI
from addic7ed_cli.error import Error, FatalError
from addic7ed_cli.login import set_session, get_current_user


class Arguments(object):

    @staticmethod
    def get_paths():
        # Linux and OSX:
        paths = [
            os.path.join(os.path.expanduser('~'), '.config', 'addic7ed'),
            os.path.join(os.path.expanduser('~'), '.addic7ed'),
        ]

        # Windows
        if 'APPDATA' in os.environ:
            paths.insert(0, os.path.join(os.environ['APPDATA'], 'config'))

        return paths

    def read_defaults(self):

        config = self.get_configparser()

        def getflag(name, default=False):
            if not config.has_section('flags') or \
                    not config.has_option('flags', name):
                return default

            value = config.get('flags', name)
            if isinstance(value, basestring):
                return config.getboolean('flags', name)

            return value is None

        self.verbose = getflag('verbose')
        self.hearing_impaired = getflag('hearing-impaired')
        self.batch = getflag('batch')
        self.brute_batch = getflag('brute-batch')
        self.overwrite = getflag('overwrite')
        self.ignore = getflag('ignore')

        if config.has_section('languages'):
            self._language = [l for l, v in config.items('languages')
                              if v is not False]
        else:
            self._language = []

        if config.has_section('session') and config.items('session'):
            self.session = config.items('session')[0][0]
        else:
            self.session = False

    def save_session(self):
        config = self.get_configparser()

        if self.session:
            if not config.has_section('session'):
                config.add_section('session')

            config.set('session', self.session, None)

        elif config.has_section('session'):
            config.remove_section('session')

        with open(self.configuration_path, 'w') as fp:
            config.write(fp)

    @property
    def configuration_path(self):
        paths = self.get_paths()
        valid_paths = (path for path in paths if os.path.isfile(path))
        return next(valid_paths, paths[0])

    def get_configparser(self):
        configuration_path = self.configuration_path
        config = configparser.ConfigParser(allow_no_value=True)
        if os.path.isfile(configuration_path):
            config.read(configuration_path)
        return config

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, language):
        if language:
            self._language = language


class ArgumentParser(object):

    _parser = None
    _subparsers = None

    def __init__(self, **kwargs):
        self._parser = argparse.ArgumentParser(**kwargs)
        self._arggroup = self._parser
        self._root_parser = self._parser
        self.first_candidates = ['-h', '--help']

    def configure_subparser(self, **kwargs):
        if self._subparsers is None:
            self._subparsers = self._parser.add_subparsers(**kwargs)

    def add_subparser(self, name, *args, **kwargs):
        self._parser = self._subparsers.add_parser(name, *args, **kwargs)
        self._arggroup = self._parser
        self.first_candidates.append(name)

    def add_argument(self, *names, **kwargs):
        self._arggroup.add_argument(*names, **kwargs)
        if self._arggroup == self._root_parser:
            self.first_candidates.extend(names)

    def add_argument_group(self, *args, **kwargs):
        self._arggroup = self._parser.add_argument_group(*args, **kwargs)

    def parse_args(self, *args, **kwargs):
        self._root_parser.parse_args(*args, **kwargs)

    def print_usage(self):
        self._root_parser.print_usage()


def search(arguments):
    SearchUI(arguments).launch()


def login(arguments):
    LoginUI(arguments).launch()


def logout(arguments):
    LogoutUI(arguments).launch()


def main():

    import textwrap
    import pkg_resources
    import sys

    version = pkg_resources.require('addic7ed-cli')[0].version

    epilog = '''
    Authentification:

      You can login with your addic7ed.com identifiers to increase your daily
      download quota:

      * Anonymous users are limited to 15 downloads per 24 hours on their IP
        address

      * Registered users are limited to 40

      * VIPs get 80 downloads (please consider donating)

    Configuration file:

      You can store frequently used options in a configuration file. Create a
      file at ~/.config/addic7ed (Linux, OSX) or %APPDATA%/config (Windows),
      and it will be parsed using the Python ConfigParser (see example below).
      It can contain three sections:

      * [flags], to set a flag (verbose, hearing-impaired, overwrite, ignore,
        batch or brute-batch)

      * [languages], to list prefered languages

      * [session], the session to use for authentification

      Example:

        [flags]
        hearing-impaired = no
        batch

        [languages]
        french
        english

        [session]
        abcdef

    Video organizer:
      video-organizer format is supported. If a "filelist" file is next to an
      episode, it will use it to extract its real name and forge the good
      query. See https://github.com/JoelSjogren/video-organizer for further
      informations.
    '''

    parser = ArgumentParser(
        description='Downloads SRT files from addic7ed.com.',
        epilog=textwrap.dedent(epilog),
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-V', '--version', action='version',
                        version='%%(prog)s version %s' % version)

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print some debugging informations.')

    parser.configure_subparser(help='Command to run. If no command is given, '
                               'the default is "search".',
                               dest='command')

    parser.add_subparser('search',
                         help='Search for a subtitle and download it')

    parser.add_argument('file', nargs='+',
                        help='Subtitle file name. The extension will be '
                        'replaced by .srt, so an existing video file name '
                        'can be given.')

    parser.add_argument('-q', '--query',
                        help='Custom query. (default: based on the filename)')

    parser.add_argument('-r', '--release',
                        help='Custom release. (default: based on the '
                        'filename)')

    parser.add_argument('-l', '--language', action='append', default=[],
                        help='Prefer a language. (could be specified more '
                        'than one time for fallbacks)')

    parser.add_argument('-H', '--hearing-impaired', action='store_true',
                        help='Prefer hearing impaired version.')

    parser.add_argument('--no-hearing-impaired', dest='hearing_impaired',
                        action='store_false')

    parser.add_argument('-o', '--overwrite', action='store_true',
                        help='Always overwrite the SRT if it exists.')

    parser.add_argument('-i', '--ignore', action='store_true',
                        help='Never overwrite the SRT if it exists.')

    parser.add_argument('-b', '--batch', action='store_true',
                        help='Do not ask anything, get the best matching '
                        'subtitle. Cancel if the search returns more than one '
                        'result.')

    parser.add_argument('-bb', '--brute-batch', action='store_true',
                        help='Do not ask anything, get the best matching '
                        'subtitle. Use the first result of the search.')

    parser.add_subparser('login',
                         help='Login on addic7ed.com. This is not required.')

    parser.add_subparser('logout',
                         help='Logout from addic7ed.com.')
    args = sys.argv[1:]

    if args and args[0] not in parser.first_candidates:
        args[0:0] = ('search',)

    namespace = Arguments()
    namespace.read_defaults()

    parser.parse_args(args=args, namespace=namespace)

    if not namespace.command:
        parser.print_usage()
        exit(1)

    if namespace.session:
        set_session(namespace.session)
        user = get_current_user()
        if user:
            echo('Logged as', user)

    try:
        globals()[namespace.command](namespace)

    except Error as e:
        echo('Error:', e)
        exit(1)

    except FatalError as e:
        echo('Fatal error:', e)
        exit(1)

    except KeyboardInterrupt:
        echo('Aborted by user')
        exit(1)


if __name__ == '__main__':
    main()
