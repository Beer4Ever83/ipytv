import unittest

from tests import test_data
from ipytv import m3u


class TestM3U(unittest.TestCase):

    def test_is_m3u_plus_extinf_string(self):
        extinf_string = '''#EXTINF:-1 tvg-id="" tvg-name="Io, Leonardo (2019)" tvg-logo="https://image.tmdb.org/t/p/w600_and_h900_bestv2/6DfpPu4iGrBswsyLdJlCwiLCudw.jpg" group-title="Recenti e Oggi al Cinema",Io, Leonardo (2019)'''
        self.assertTrue(m3u.is_m3u_plus_extinf_row(extinf_string))

    def test_is_not_m3u_plus_extinf_string(self):
        extinf_string = '''#EXTINF:-1,SANTUÁRIO DE FÁTIMA'''
        self.assertFalse(m3u.is_m3u_plus_extinf_row(extinf_string))

    def test_is_m3u_extinf_string(self):
        extinf_string = '''#EXTINF:-1,SANTUÁRIO DE FÁTIMA'''
        self.assertTrue(m3u.is_m3u_extinf_row(extinf_string))

    def test_is_not_m3u_extinf_string(self):
        extinf_string = '''#EXTINF:-1 tvg-id="" tvg-name="Io, Leonardo (2019)" tvg-logo="https://image.tmdb.org/t/p/w600_and_h900_bestv2/6DfpPu4iGrBswsyLdJlCwiLCudw.jpg" group-title="Recenti e Oggi al Cinema",Io, Leonardo (2019)'''
        self.assertFalse(m3u.is_m3u_extinf_row(extinf_string))

    def test_match_m3u_plus_broken_extinf_string(self):
        self.assertNotEqual(None, m3u.match_m3u_plus_broken_extinf_row(test_data.broken_extinf_row))

    def test_get_m3u_plus_broken_attributes(self):
        attributes = m3u.get_m3u_plus_broken_attributes(test_data.broken_extinf_row)
        for name, value in test_data.expected_attributes_broken_extinf_row.items():
            self.assertEqual(value, attributes[name])


if __name__ == '__main__':
    unittest.main()
