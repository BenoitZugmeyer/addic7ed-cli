#!/usr/bin/python2

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import os.path

from addic7ed.compat import echo, basestring
from addic7ed.ui import UI
from addic7ed.error import Error, FatalError


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

    try:
        for file in args.file:
            try:
                UI(args, file).launch()
            except Error as e:
                echo('Error:', e)

    except FatalError as e:
        echo('Fatal error:', e)
        exit(1)

    except KeyboardInterrupt:
        echo('Aborted by user')
        exit(1)


if __name__ == '__main__':
    main()
