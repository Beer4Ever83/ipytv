import unittest

import test_data
from ipytv import m3u


class TestIsM3UPlusExtinfString(unittest.TestCase):
    def runTest(self):
        extinf_string = '''#EXTINF:-1 tvg-id="" tvg-name="Io, Leonardo (2019)" tvg-logo="https://image.tmdb.org/t/p/w600_and_h900_bestv2/6DfpPu4iGrBswsyLdJlCwiLCudw.jpg" group-title="Recenti e Oggi al Cinema",Io, Leonardo (2019)'''
        self.assertTrue(m3u.is_m3u_plus_extinf_row(extinf_string))


class TestIsNotM3UPlusExtinfString(unittest.TestCase):
    def runTest(self):
        extinf_string = '''#EXTINF:-1,SANTUÁRIO DE FÁTIMA'''
        self.assertFalse(m3u.is_m3u_plus_extinf_row(extinf_string))


class TestIsM3UExtinfString(unittest.TestCase):
    def runTest(self):
        extinf_string = '''#EXTINF:-1,SANTUÁRIO DE FÁTIMA'''
        self.assertTrue(m3u.is_m3u_extinf_row(extinf_string))


class TestIsNotM3UExtinfString(unittest.TestCase):
    def runTest(self):
        extinf_string = '''#EXTINF:-1 tvg-id="" tvg-name="Io, Leonardo (2019)" tvg-logo="https://image.tmdb.org/t/p/w600_and_h900_bestv2/6DfpPu4iGrBswsyLdJlCwiLCudw.jpg" group-title="Recenti e Oggi al Cinema",Io, Leonardo (2019)'''
        self.assertFalse(m3u.is_m3u_extinf_row(extinf_string))


class TestMatchM3UPlusBrokenExtinfString(unittest.TestCase):
    def runTest(self):
        self.assertNotEqual(None, m3u.match_m3u_plus_broken_extinf_row(test_data.broken_extinf_row))


class TestGetM3UPlusBrokenAttributes(unittest.TestCase):
    def runTest(self):
        attributes = m3u.get_m3u_plus_broken_attributes(test_data.broken_extinf_row)
        for name, value in test_data.expected_attributes_broken_extinf_row.items():
            self.assertEqual(value, attributes[name])


if __name__ == '__main__':
    unittest.main()
