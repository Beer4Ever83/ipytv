import os
import shutil
import unittest
from typing import List

from ipytv import playlist
from ipytv.playlist import M3UPlaylist
from ipytv.utils import extract_series, extract_show_name, is_episode_from_series

pl_list = [
    '#EXTM3U pl-attribute="pl-attributed-value"',
    '#EXTINF:-1 group-title="Unlikely Series",The Talking Dead S01 E01',
    'https://myserver.com/series/the-talking-dead-s01e01.mp4',
    '#EXTINF:-1 group-title="Unlikely Series",The Talking Dead S01 E02',
    'https://myserver.com/series/the-talking-dead-s01e02.mp4',
    '#EXTINF:-1 group-title="Unlikely Series",The Talking Dead S01 E03',
    'https://myserver.com/series/the-talking-dead-s01e03.mp4',
    '#EXTINF:-1 group-title="Unlikely Movies",The Dark Might',
    'https://myserver.com/series/the-dark-might.mp4',
    '#EXTINF:-1 group-title="Unlikely Series",Baking Bread s01e01',
    'https://myserver.com/series/baking-bread-s01e01.mp4',
    '#EXTINF:-1 group-title="Unlikely Series",Baking Bread s01e02',
    'https://myserver.com/series/baking-bread-s01e02.mp4',
    '#EXTINF:-1 group-title="Unlikely Series",Baking Bread s01e03',
    'https://myserver.com/series/baking-bread-s01e03.mp4',
    '#EXTINF:-1 group-title="Unlikely Series",Formula 1: Drunk To Survive S01 E01',
    'https://myserver.com/series/drunk-to-survive-s01e01.mp4',
    '#EXTINF:-1 group-title="Unlikely Series",Prey\'s Anatomy S01 E01',
    'https://myserver.com/series/prey-s-anatomy-s01e01.mp4',
    '#EXTINF:-1 group-title="Unlikely Movies",Schindler\'s Fist',
    'https://myserver.com/series/schindler-s-fist.mp4',
    '#EXTINF:-1 group-title="Unlikely Series",Crappy Days 02x01 - The Bonz',
    'https://myserver.com/series/crappy-days-s02e01.mp4',
    '#EXTINF:-1 group-title="Unlikely Series",Crappy Days 02x02 - Richie Moves On',
    'https://myserver.com/series/crappy-days-s02e02.mp4'
]
pl = playlist.loadl(pl_list)


class TestUtils(unittest.TestCase):
    def test_extract_series(self) -> None:
        series_map, not_series = extract_series(pl, exclude_single=False)
        self.assertEqual(2, not_series.length())
        self.assertEqual(5, len(series_map))
        self.assertEqual(3, series_map["the talking dead"].length())
        self.assertEqual(3, series_map["baking bread"].length())
        self.assertEqual(1, series_map["formula 1: drunk to survive"].length())
        self.assertEqual(1, series_map["prey's anatomy"].length())
        self.assertEqual(2, series_map["crappy days"].length())


    def test_extract_series_no_single(self) -> None:
        series_map, not_series = extract_series(pl, exclude_single=True)
        self.assertEqual(2, not_series.length())
        self.assertEqual(3, len(series_map))
        self.assertEqual(3, series_map["the talking dead"].length())
        self.assertEqual(3, series_map["baking bread"].length())
        self.assertFalse("formula 1: drunk to survive" in series_map)
        self.assertFalse("prey's anatomy" in series_map)
        self.assertEqual(2, series_map["crappy days"].length())


    def test_extract_show_name_format_1(self) -> None:
        shows = [
            "The Talking Dead S01 E01",
            "The Talking Dead s01 e01",
            "The Talking Dead S01 e01",
            "The Talking Dead s01 E01",
            "The Talking Dead S01E01",
            "The Talking Dead s01e01",
            "The Talking Dead S01e01",
            "The Talking Dead s01E01",
            "The Talking Dead E01",
            "The Talking Dead e01",
        ]
        # Check that the show name is extracted correctly regardless of the case of the letters and the spaces
        for show in shows:
            self.assertEqual("The Talking Dead", extract_show_name(show))
        # Check that the season numbers from 01 to 99 and episode numbers from 01 to 999 are correctly handled
        for season in range(1, 100):
            for episode in range(1, 1000):
                show = f"The Talking Dead S{season:0>2d} E{episode:0>2d}"
                self.assertEqual("The Talking Dead", extract_show_name(show))


    def test_extract_show_name_format_2(self) -> None:
        shows = [
            "The Talking Dead 01x01",
            "The Talking Dead 01.01",
            "The Talking Dead 1x1",
            "The Talking Dead 1.1",
        ]
        # Check that the show name is extracted correctly regardless of the case of the letters and the spaces
        for show in shows:
            self.assertEqual("The Talking Dead", extract_show_name(show))
        # Check that the season numbers from 01 to 99 and episode numbers from 01 to 999 are correctly handled
        for season in range(1, 100):
            for episode in range(1, 1000):
                show = f"The Talking Dead {season:0>2d}x{episode:0>2d}"
                self.assertEqual("The Talking Dead", extract_show_name(show))


    def test_extract_show_name_format_3(self) -> None:
        shows = [
            "The Talking Dead.01",
            "The Talking Dead.1",
        ]
        # Check that the show name is extracted correctly regardless of the case of the letters and the spaces
        for show in shows:
            self.assertEqual("The Talking Dead", extract_show_name(show))
        # Check that episode numbers from 01 to 999 are correctly handled
        for episode in range(1, 1000):
            show = f"The Talking Dead.{episode:0>2d}"
            self.assertEqual("The Talking Dead", extract_show_name(show))


    def test_is_episode_from_series(self) -> None:
        tests = [
            {"title": "The Talking Dead.01", "is_series": True},
            {"title": "The Talking Dead", "is_series": False},
            {"title": "The Talking Dead 24.03.2020", "is_series": False},
            {"title": "The Talking Dead 1920x1024", "is_series": False},
            {"title": "Premium.1", "is_series": True},
            {"title": "Formula 1", "is_series": False},
            {"title": "Antenna1", "is_series": False},
            {"title": "", "is_series": False},
            {"title": "Crappy Days 01x25 - The Bonz", "is_series": True},
            {"title": "Crappy Days S01 E25 - The Bonz", "is_series": True},
            {"title": "Crappy Days E25 - The Bonz", "is_series": True},
            {"title": "Crappy Days.25", "is_series": True},
            {"title": "Crappy Days.25 - The Bonz", "is_series": False},
        ]
        # Check that the show name is extracted correctly regardless of the case of the letters and the spaces
        for test in tests:
            self.assertTrue(is_episode_from_series(test["title"]) is test["is_series"], f"Failed for {test['title']}")


if __name__ == '__main__':
    unittest.main()
