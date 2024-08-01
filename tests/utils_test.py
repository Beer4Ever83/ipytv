import unittest

from ipytv.channel import IPTVChannel
from ipytv.playlist import M3UPlaylist
from ipytv.utils import is_good_fit


class TestUtils(unittest.TestCase):
    def test_is_good_fit(self):
        ch = IPTVChannel(name="The Walking Dead S11E22")
        pl = M3UPlaylist()
        pl.append_channel(IPTVChannel(name="The Walking Dead S01E01"))
        pl.append_channel(IPTVChannel(name="the walking dead S01E02"))
        pl.append_channel(IPTVChannel(name="The Walking Dead S01 E03"))
        pl.append_channel(IPTVChannel(name="the walking dead S:01 E03"))
        self.assertTrue(is_good_fit(ch, pl))  # add assertion here


if __name__ == '__main__':
    unittest.main()
