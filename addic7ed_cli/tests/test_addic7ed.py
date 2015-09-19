from unittest import TestCase

from addic7ed_cli.episode import Episode, search
from addic7ed_cli.util import file_to_query, normalize_release


def s(*args):
    return set(args)


class TestAddic7ed(TestCase):

    maxDiff = None

    def test_search(self):
        result = search('homeland 2x02')
        self.assertEqual(result, [
            Episode(
                'http://www.addic7ed.com/serie/Homeland/2/2/Beirut_Is_Back',
                'Homeland - 02x02 - Beirut Is Back')
        ])

    def test_search_multiple(self):
        result = search('black mirror 01x')
        self.assertEqual(result, [
            Episode(
                'serie/Black_Mirror_%25282011%2529/1/1/The_National_Anthem',
                'Black Mirror (2011) - 01x01 - The National Anthem'),
            Episode(
                'serie/Black_Mirror_%25282011%2529/1/2/15_Million_Merits',
                'Black Mirror (2011) - 01x02 - 15 Million Merits'),
            Episode(
                'serie/Black_Mirror_%25282011%2529/1/3/'
                'The_Entire_History_of_You',
                'Black Mirror (2011) - 01x03 - The Entire History of You'),
        ])

    def file_to_query(self, filename, query, version=set()):
        q, v = file_to_query(filename)
        self.assertEqual(query, q)
        self.assertEqual(version, v)

    def test_file_to_query(self):
        self.file_to_query('Homeland.S02E02.PROPER.720p.HDTV.x264-EVOLVE.mkv',
                           'homeland 2x02',
                           s('proper', 'evolve'))
        self.file_to_query('CSI.S13E06.720p.HDTV.X264-DIMENSION.mkv',
                           'csi 13x06',
                           s('dimension', 'sys', 'lol'))
        self.file_to_query('Youre.the.Worst.S02E02.720p.HDTV.X264-DIMENSION[EtHD].mkv',
                           "you're the worst 2x02",
                           s('dimension', 'sys', 'lol'))

    def test_file_to_query_stopword(self):
        self.file_to_query('Foo.and.Bar.S02E23.PLOP.mkv',
                           'foo bar 2x23',
                           s('plop'))

    def test_file_to_query_exceptions(self):
        self.file_to_query('CSI.New.York.S09E10.720p.HDTV.X264-YOLO.mkv',
                           'csi ny 9x10',
                           s('yolo'))

    def test_file_to_query_number_in_title(self):
        self.file_to_query('Dont.Apartment.23.S02E05.720p.HDTV.X264'
                           '-DIMENSION.mkv',
                           'don\'t apartment 23 2x05',
                           s('dimension', 'sys', 'lol'))

    def test_file_to_query_noseason(self):
        self.file_to_query('Foo.23.mkv', 'foo 23')

    def test_file_to_query_nonumber(self):
        self.file_to_query('Foo bar.mkv', 'foo bar', s('foo', 'bar'))

    def test_file_to_query_threenumbers(self):
        self.file_to_query('The.Serie.223.MDR.mkv', 'the serie 2x23', s('mdr'))
        self.file_to_query('hannibal.210.hdtv-lol', 'hannibal 2x10')

    def test_file_to_query_season_episode(self):
        self.file_to_query('The Serie Season 4 Episode 03 - Foo',
                           'the serie 4x03', s('foo'))

    def test_episode(self):
        result = Episode('serie/Homeland/2/2/Beirut_Is_Back')
        result.fetch_versions()
        self.assertEqual(result.title, 'Homeland - 02x02 - Beirut Is Back')
        versions = result.filter_versions(['english', 'french'], s('evolve'))
        self.assertEqual('English', versions[1].language)
        self.assertEqual('/original/67365/2', versions[1].url)
        self.assertFalse(versions[0].hearing_impaired)
        self.assertTrue(versions[1].hearing_impaired)

    def test_unicode_episode(self):
        search('family guy 10x12')[0].fetch_versions()

        # doing another query after that should not raise any exception
        search('family guy 10x11')

    def test_normalize_release(self):
        self.assertEqual(s('immerse', 'asap', 'xii'),
                         normalize_release(s('immerse', '720p')))

        self.assertEqual(s('lol', 'sys', 'dimension'),
                         normalize_release(s('lol')))
        self.assertEqual(s('mdr'), normalize_release(s('mdr')))
