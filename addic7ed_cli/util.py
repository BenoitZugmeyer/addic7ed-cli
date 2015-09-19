import os
import re
import xml.etree.ElementTree as ET

from addic7ed_cli.compat import echo


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
    filename, ext = os.path.splitext(filename)
    if ext in ('.part', '.!qB'):
        filename, ext = os.path.splitext(filename)
    return filename


def normalize_whitespace(string):
    # change extra characters to space
    return re.sub(r'[\s._,-]+', ' ', string).strip()


def string_set(string):
    string = normalize_whitespace(string.lower())
    return set(string.split(' ')) if string else set()


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
    basename = re.sub(r'\byoure\b', 'you\'re', basename)
    basename = re.sub(r'\bcsi new york\b', 'csi ny', basename)

    episode = re.search(r'season\s+0*(\d+)\s+episode\s+(\d+)',
                        basename, re.I) or \
        re.search(r'\S*?0*(\d+)[xe](\d+)', basename) or \
        re.search(r'()(\d+)', basename)

    if episode:
        index = basename.find(episode.group(0))
        release = basename[index + len(episode.group(0)):]
        basename = basename[:index]
        season = episode.group(1)
        number = episode.group(2)

        if not season and len(number) >= 3:
            season = number[0]
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


def get_file_alias(filename):

    directory, basename = os.path.split(filename)

    filelist_path = os.path.join(directory, 'filelist')

    if os.path.isfile(filelist_path):
        basename = remove_extension(basename)
        try:
            tree = ET.parse(filelist_path)
        except Exception as e:
            echo('Warning: unable to parse {}: {}'.format(filelist_path, e))
        else:
            for record in tree.findall('.//record'):
                if remove_extension(record.get('to')) == basename:
                    return record.get('from')

    return filename
