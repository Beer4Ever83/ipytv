import unittest

import test_data
from ipytv import m3u


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
