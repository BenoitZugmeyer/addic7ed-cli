from unittest import TestCase

import addic7ed
#from pprint import pprint

s = lambda *args: set(args)


class TestAddic7ed(TestCase):

    maxDiff = None

    def test_search(self):
        result = addic7ed.Episode.search('homeland 2x02')
        self.assertEqual(result, [
            addic7ed.Episode('serie/Homeland/2/2/Beirut_Is_Back',
                             'Homeland - 02x02 - Beirut Is Back')
        ])

    def test_file_to_query(self):
        filename = 'Homeland.S02E02.PROPER.720p.HDTV.x264-EVOLVE.mkv'
        query, version = addic7ed.file_to_query(filename)
        self.assertEqual(query, 'homeland 2x02')
        self.assertEqual(version, s('proper', '720p', 'hdtv', 'x264',
                                    'evolve'))

    def test_file_to_query_stopword(self):
        filename = 'Foo.and.Bar.S02E23.PLOP.mkv'
        query, version = addic7ed.file_to_query(filename)
        self.assertEqual(query, 'foo bar 2x23')
        self.assertEqual(version, s('plop'))

    def test_file_to_query_exceptions(self):
        query = addic7ed.file_to_query(
            'CSI.New.York.S09E10.720p.HDTV.X264-YOLO.mkv'
        )[0]
        self.assertEqual(query, 'csi ny 9x10')

    def test_file_to_query_number_in_title(self):
        filename = 'Dont Apartment.23.S02E05.720p.HDTV.X264-DIMENSION.mkv'
        query, version = addic7ed.file_to_query(filename)
        self.assertEqual(query, 'don\'t apartment 23 2x05')
        self.assertEqual(version, s('720p', 'hdtv', 'x264', 'dimension'))

    def test_file_to_query_noseason(self):
        filename = 'Foo.23.mkv'
        query, version = addic7ed.file_to_query(filename)
        self.assertEqual(query, 'foo 23')
        self.assertEqual(version, s())

    def test_file_to_query_nonumber(self):
        filename = 'Foo bar.mkv'
        query, version = addic7ed.file_to_query(filename)
        self.assertEqual(query, 'foo bar')
        self.assertEqual(version, s('foo', 'bar'))

    def test_episode(self):
        result = addic7ed.Episode('serie/Homeland/2/2/Beirut_Is_Back')
        result.fetch_versions()
        self.assertEqual(result.title, 'Homeland - 02x02 - Beirut Is Back')
        versions = result.filter_versions(['english', 'french'], s('evolve'))
        self.assertEqual('English', versions[1].language)
        self.assertEqual('/original/67365/2', versions[1].url)
        self.assertFalse(versions[0].hearing_impaired)
        self.assertTrue(versions[1].hearing_impaired)

    def test_complete_release(self):
        self.assertEqual(s('immerse', 'asap', 'xii', '720p'),
                         addic7ed.complete_release(s('immerse', '720p')))

        self.assertEqual(s('lol', 'sys', 'dimension'),
                         addic7ed.complete_release(s('lol')))
        self.assertEqual(s('mdr'), addic7ed.complete_release(s('mdr')))
