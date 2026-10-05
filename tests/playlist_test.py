import copy
import itertools
import json
import multiprocessing as mp
import os
import re
import tempfile
import unittest
from unittest import mock

import m3u8
import requests
import responses
from deepdiff import DeepDiff

import ipytv.playlist as playlist
from ipytv import m3u
from ipytv.channel import IPTVAttr, IPTVChannel
from ipytv.exceptions import (
    AttributeAlreadyPresentException,
    AttributeNotFoundException,
    IndexOutOfBoundsException,
    IPyTVException,
    MalformedPlaylistException,
    URLException,
    WrongTypeException,
)
from ipytv.playlist import M3UPlaylist
from tests import test_data


def produce_singles(n: int) -> list[str]:
    out: list[str] = []
    for i in range(n):
        row = f"https://www.mywebsite.com/video/myvideo{i}.mp4"
        out.append(row)
    return out


def produce_doubles(n: int) -> list[str]:
    out: list[str] = []
    for i in range(n):
        row_1 = f'#EXTINF:-1 tvg-id="id_{i}" tvg-name="name_{i}" tvg-language="Italian" tvg-logo="https://i.imgur.com/{1}.png" tvg-country="IT" tvg-url="" group-title="Group",Channel {i}'
        out.append(row_1)
        row_2 = f"https://www.mywebsite.com/video/myvideo{i}.mp4"
        out.append(row_2)
    return out


def produce_triples(n: int) -> list[str]:
    out: list[str] = []
    for i in range(n):
        row_1 = f'#EXTINF:-1 tvg-id="id_{i}" tvg-name="name_{i}" tvg-language="Italian" tvg-logo="https://i.imgur.com/{1}.png" tvg-country="IT" tvg-url="" group-title="Group",Channel {i}'
        out.append(row_1)
        row_2 = f"#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.{i}"
        out.append(row_2)
        row_3 = f"https://www.mywebsite.com/video/myvideo{i}.mp4"
        out.append(row_3)
    return out


class InProcessPool:
    """Stand-in for multiprocessing.Pool that runs the tasks synchronously and records their arguments."""

    def __init__(self, processes: int | None = None) -> None:
        self.task_args: list[tuple] = []

    def __enter__(self) -> "InProcessPool":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def apply_async(self, func, args):
        self.task_args.append(args)
        result = func(*args)
        return mock.Mock(get=mock.Mock(return_value=result))


ALWAYS_PARALLEL = {"fork": 0, "forkserver": 0, "spawn": 0}


def strip_blank_lines(rows: list) -> list:
    return list(itertools.filterfalse(m3u.is_empty_row, rows))


def count_extras(pl: M3UPlaylist) -> int:
    amount = 0
    for ch in pl:
        amount += len(ch.extras)
    return amount


class TestM3UPlaylist(unittest.TestCase):
    def test_chunk_body_below_the_minimum_chunk_size(self):
        body = produce_singles(50)
        self.assertEqual([{"beginning": 0, "end": 49}], playlist._chunk_body(body, 4))

    def test_chunk_body_0(self):
        body = produce_singles(5)  # total 05 rows
        body += produce_doubles(4)  # total 13 rows
        body += produce_triples(5)  # total 28 rows
        chunks = playlist._chunk_body(body, 2, enforce_min_size=False)
        self.assertEqual(2, len(chunks))
        self.assertEqual({"beginning": 0, "end": 15}, chunks[0])
        self.assertEqual({"beginning": 16, "end": 27}, chunks[1])

    def test_chunk_body_1(self):
        body = produce_singles(5)  # total 05 rows
        body += produce_doubles(4)  # total 13 rows
        body += produce_triples(5)  # total 28 rows
        chunks = playlist._chunk_body(body, 3, enforce_min_size=False)
        self.assertEqual(3, len(chunks))
        self.assertEqual({"beginning": 0, "end": 10}, chunks[0])
        self.assertEqual({"beginning": 11, "end": 21}, chunks[1])
        self.assertEqual({"beginning": 22, "end": 27}, chunks[2])

    def test_chunk_body_2(self):
        body = produce_singles(50)  # total 50 rows
        chunks = playlist._chunk_body(body, 5, enforce_min_size=False)
        self.assertEqual(5, len(chunks))
        self.assertEqual({"beginning": 0, "end": 9}, chunks[0])
        self.assertEqual({"beginning": 10, "end": 19}, chunks[1])
        self.assertEqual({"beginning": 20, "end": 29}, chunks[2])
        self.assertEqual({"beginning": 30, "end": 39}, chunks[3])
        self.assertEqual({"beginning": 40, "end": 49}, chunks[4])

    def test_chunk_body_3(self):
        body = produce_singles(5)  # total 5 rows
        chunks = playlist._chunk_body(body, 5, enforce_min_size=False)
        self.assertEqual(5, len(chunks))
        self.assertEqual({"beginning": 0, "end": 0}, chunks[0])
        self.assertEqual({"beginning": 1, "end": 1}, chunks[1])
        self.assertEqual({"beginning": 2, "end": 2}, chunks[2])
        self.assertEqual({"beginning": 3, "end": 3}, chunks[3])
        self.assertEqual({"beginning": 4, "end": 4}, chunks[4])

    def test_chunk_body_4(self):
        body = produce_singles(5)  # total 5 rows
        body += produce_triples(1)  # total 8 rows
        body += produce_singles(5)  # total 13 rows
        chunks = playlist._chunk_body(body, 2, enforce_min_size=False)
        self.assertEqual(2, len(chunks))
        self.assertEqual({"beginning": 0, "end": 7}, chunks[0])
        self.assertEqual({"beginning": 8, "end": 12}, chunks[1])

    def test_chunk_body_5(self):
        body = produce_doubles(3)  # total 6 rows
        body += produce_triples(1)  # total 9 rows
        body += produce_doubles(3)  # total 15 rows
        chunks = playlist._chunk_body(body, 4, enforce_min_size=False)
        self.assertEqual(4, len(chunks))
        self.assertEqual({"beginning": 0, "end": 3}, chunks[0])
        self.assertEqual({"beginning": 4, "end": 8}, chunks[1])
        self.assertEqual({"beginning": 9, "end": 12}, chunks[2])
        self.assertEqual({"beginning": 13, "end": 14}, chunks[3])

    def test_loadl_m3u_plus_huge(self):
        filename = "tests/resources/m3u_plus.m3u"
        # factor is the amount of copies of the content of the file we want to parse
        factor = 100000
        # there are 4 channels in the file
        expected_length = 4 * factor
        with open(filename, encoding="utf-8") as file:
            buffer = file.readlines()
            new_buffer = [buffer[0]]
            # Let's copy the same content over and over again
            for _ in range(factor):
                new_buffer += buffer[1:]
        pl = playlist.loadl(new_buffer)
        self.assertEqual(expected_length, pl.length(), "The size of the playlist is not the expected one")

    def test_loaders_reject_wrong_types(self):
        loaders = [playlist.loadl, playlist.loads, playlist.loadf, playlist.loadu, playlist.loadj, playlist.loadjstr]
        for loader in loaders:
            with self.subTest(loader=loader.__name__), self.assertRaises(WrongTypeException):
                loader(42)  # type: ignore[arg-type]

    def test_loadl_without_rows(self):
        for rows in ([], ["", "   "]):
            with self.subTest(rows=rows), self.assertRaises(MalformedPlaylistException):
                playlist.loadl(rows)

    def test_loadl_without_header(self):
        with self.assertRaises(MalformedPlaylistException):
            playlist.loadl(['#EXTINF:-1 tvg-id="a",Channel', "http://a"])

    def test_loadl_with_adjacent_extinf_rows(self):
        pl = playlist.loadl(["#EXTM3U", '#EXTINF:-1 tvg-id="a",No URL', '#EXTINF:-1 tvg-id="b",With URL', "http://b"])
        self.assertEqual(
            [
                IPTVChannel(name="No URL", attributes={"tvg-id": "a"}),
                IPTVChannel(url="http://b", name="With URL", attributes={"tvg-id": "b"}),
            ],
            pl.get_channels(),
        )

    def test_loadl_m3u_plus_empty_playlist(self):
        pl = playlist.loadl(["#EXTM3U", ""])
        self.assertEqual(0, pl.length(), "The size of the playlist is not the expected one")

    def test_loadl_m3u_plus_with_extras(self):
        checks: list[dict[str, list[str]]] = [
            {
                "input_rows": [
                    "#EXTM3U",
                    "#EXTRAS0:",
                    '#EXTINF:-1 tvg-id="MTV" group-title="Music",MTV',
                    "https://myownurl.com/playlist0.m3u8",
                    "",
                    "#EXTRAS1:",
                    '#EXTINF:-1 tvg-id="MTV+1" group-title="Music",MTV+1',
                    "https://myownurl.com/playlist1.m3u8",
                ],
                "expected_channels": 2,
                "expected_extras": 2,
            },
            {
                "input_rows": [
                    "#EXTM3U",
                    "https://myownurl.com/playlist0.m3u8",
                    "https://myownurl.com/playlist1.m3u8",
                    "",
                    "#EXTRAS0:",
                    '#EXTINF:-1 tvg-id="MTV+1" group-title="Music",MTV+1',
                    "https://myownurl.com/playlist2.m3u8",
                ],
                "expected_channels": 3,
                "expected_extras": 1,
            },
            {
                "input_rows": [
                    "#EXTM3U",
                    "",
                    "#EXTRAS0:",
                    "#EXTRAS1:",
                    "#EXTRAS2:",
                    "https://myownurl.com/playlist0.m3u8",
                    "https://myownurl.com/playlist1.m3u8",
                    "",
                    "#EXTRAS3:",
                    '#EXTINF:-1 tvg-id="MTV+1" group-title="Music",MTV+1',
                    "https://myownurl.com/playlist2.m3u8",
                ],
                "expected_channels": 3,
                "expected_extras": 4,
            },
            {
                "input_rows": [
                    "#EXTM3U",
                    "",
                    "#EXTINF:-1,Name",
                    "#EXTRAS0:",
                    "#EXTRAS1:",
                    "#EXTRAS2:",
                    "https://myownurl.com/playlist0.m3u8",
                    "#EXTRAS3:",
                    "#EXTINF:-1,Name",
                    "https://myownurl.com/playlist1.m3u8",
                    "",
                    "#EXTRAS4:",
                    '#EXTINF:-1 tvg-id="MTV+1" group-title="Music",MTV+1',
                    "https://myownurl.com/playlist2.m3u8",
                    "#EXTINF:-1,Name",
                    "https://myownurl.com/playlist3.m3u8",
                ],
                "expected_channels": 4,
                "expected_extras": 5,
            },
        ]
        for c in checks:
            input_rows = c["input_rows"]
            expected_channels = c["expected_channels"]
            expected_extras = c["expected_extras"]
            pl = playlist.loadl(input_rows)
            self.assertEqual(expected_channels, pl.length(), "The size of the playlist is not the expected one")
            self.assertEqual(expected_extras, count_extras(pl), "The size of the extras is not the expected one")

    def test_loadf_m3u_plus(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        self.assertEqual(test_data.expected_m3u_plus, pl, "The two playlists are not equal")

    def test_populate_with_extra_tags_logs_no_warnings(self):
        with open("tests/resources/m3u_plus.m3u", encoding="utf-8") as file:
            body = file.readlines()[1:]
        # _populate is called directly because log records from the pool workers don't reach the caller.
        with self.assertNoLogs("ipytv", level="WARNING"):
            pl = playlist._populate(body)
        self.assertTrue(any(ch.extras for ch in pl), "the test playlist should contain extra tags")

    def test_loadl_parses_small_playlists_in_process(self):
        rows = ["#EXTM3U", *produce_triples(10)]
        with mock.patch("ipytv.playlist.mp.Pool") as pool_class:
            pl = playlist.loadl(rows)
        pool_class.assert_not_called()
        self.assertEqual(playlist._populate(rows[1:]), pl)

    def test_loadl_sends_each_worker_only_its_chunk(self):
        rows = ["#EXTM3U", *produce_triples(1000)]
        body = rows[1:]
        pool = InProcessPool()
        with (
            mock.patch.dict(playlist._PARALLEL_PARSING_MIN_ROWS, ALWAYS_PARALLEL),
            mock.patch("ipytv.playlist.mp.cpu_count", return_value=4),
            mock.patch("ipytv.playlist.mp.Pool", return_value=pool),
        ):
            pl = playlist.loadl(rows)
        self.assertEqual(4, len(pool.task_args))
        self.assertEqual(len(body), sum(len(args[0]) for args in pool.task_args))
        self.assertEqual(playlist._populate(body), pl)

    def test_loadl_parallel_threshold_depends_on_the_start_method(self):
        rows = ["#EXTM3U", *produce_singles(40_000)]
        for start_method, expect_pool in (("fork", True), ("forkserver", True), ("spawn", False), (None, None)):
            with (
                self.subTest(start_method=start_method),
                mock.patch("ipytv.playlist.mp.get_start_method", return_value=start_method),
                mock.patch("ipytv.playlist.mp.Pool", return_value=InProcessPool()) as pool_class,
            ):
                pl = playlist.loadl(rows)
                if expect_pool is None:
                    # No start method set yet: the platform default decides, without fixing it as a side effect.
                    expect_pool = mp.get_all_start_methods()[0] != "spawn"
                self.assertEqual(expect_pool, pool_class.called)
                self.assertEqual(40_000, len(pl))

    def test_loadl_with_a_real_process_pool(self):
        rows = ["#EXTM3U", *produce_triples(500), *produce_singles(500), *produce_doubles(500)]
        with mock.patch.dict(playlist._PARALLEL_PARSING_MIN_ROWS, ALWAYS_PARALLEL):
            pl = playlist.loadl(rows)
        self.assertEqual(1500, len(pl))
        self.assertEqual(playlist._populate(rows[1:]), pl)

    def test_loadf_m3u8(self):
        pl = playlist.loadf("tests/resources/m3u8.m3u")
        self.assertEqual(test_data.expected_m3u8, pl, "The two playlists are not equal")

    def _load_mocked_url(self, body: str) -> M3UPlaylist:
        url = "http://myown.link:80/luke/playlist.m3u"
        with responses.RequestsMock() as mocked:
            mocked.get(url, body=body, status=200, content_type="application/octet-stream")
            return playlist.loadu(url)

    def test_loadu_m3u_plus(self):
        with open("tests/resources/m3u_plus.m3u", encoding="utf-8") as content:
            pl = self._load_mocked_url(content.read())
        self.assertEqual(test_data.expected_m3u_plus, pl, "The two playlists are not equal")

    def test_loadu_m3u_plus_with_empty_playlist(self):
        pl = self._load_mocked_url("#EXTM3U\n")
        self.assertEqual(0, pl.length(), "Expected an empty playlist")

    def test_loadu_m3u8(self):
        with open("tests/resources/m3u8.m3u", encoding="utf-8") as content:
            pl = self._load_mocked_url(content.read())
        self.assertEqual(test_data.expected_m3u8, pl, "The two playlists are not equal")

    def test_loadu_errors(self):
        error_codes = [*range(400, 419), *range(421, 427), 428, 429, 431, 451, *range(500, 509), 510, 511]
        url = "http://myown.link:80/luke/playlist.m3u"
        with responses.RequestsMock() as mocked:
            for code in error_codes:
                with self.subTest(code=code):
                    mocked.get(url, status=code)
                    self.assertRaises(URLException, playlist.loadu, url)
                    mocked.reset()

    def test_loadjstr(self):
        expected_pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        with open("tests/resources/m3u_plus.json") as json_file:
            json_str = "\n".join(json_file.readlines())
        pl = playlist.loadjstr(json_str)
        self.assertEqual(expected_pl, pl, "The two playlists are not equal")

    def test_loadjstr_with_invalid_json(self):
        with self.assertRaises(WrongTypeException):
            playlist.loadjstr("{not json")

    def test_loadu_connection_error(self):
        with (
            mock.patch("ipytv.playlist.requests.get", side_effect=requests.ConnectionError("unreachable")),
            self.assertRaises(URLException),
        ):
            playlist.loadu("http://myown.link:80/luke/playlist.m3u")

    def test_loadjstr_with_unsupported_json(self):
        with open("tests/resources/unsupported.json") as json_file:
            json_str = json_file.read()
        self.assertRaises(WrongTypeException, playlist.loadjstr, json_str)

    def test_loadjstr_from_different_cwd(self):
        # The schema is bundled with the package, so loadjstr must work
        # regardless of the current working directory.
        json_str = json.dumps(
            {
                "attributes": {"x-tvg-url": "http://example.com/guide.xml"},
                "channels": [
                    {
                        "name": "Channel 1",
                        "duration": "-1",
                        "url": "http://example.com/stream1",
                        "attributes": {},
                        "extras": [],
                    }
                ],
            }
        )
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp_dir:
            os.chdir(tmp_dir)
            try:
                pl = playlist.loadjstr(json_str)
            finally:
                os.chdir(original_cwd)
        self.assertEqual(1, pl.length())

    def test_to_m3u_plus_playlist(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        with open("tests/resources/m3u_plus.m3u") as file:
            expected_content = "".join(strip_blank_lines(file.readlines()))
            content = pl.to_m3u_plus_playlist()
            self.assertEqual(expected_content, content, "The two playlists are not equal")

    def test_to_m3u8_playlist(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl_string = pl.to_m3u8_playlist()
        pl_m3u8 = m3u8.loads(pl_string)
        pl_m3u8_string = pl_m3u8.dumps()
        self.assertEqual(pl_string, pl_m3u8_string)

    def test_to_json(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl_json = pl.to_json_playlist()
        with open("tests/resources/m3u_plus.json") as json_file:
            expected_json = json.load(json_file)
            self.assertEqual(expected_json, json.loads(pl_json))

    def test_clone(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")

        new_pl = pl.copy()
        self.assertEqual(pl, new_pl)
        new_pl.get_channels()[0].name = "mynewchannel"
        self.assertNotEqual(pl, new_pl)

        new_pl = pl.copy()
        new_pl.get_channels()[0] = IPTVChannel(name="mynewchannel", url="mynewurl")
        self.assertNotEqual(pl, new_pl)

        new_pl = pl.copy()
        new_pl.get_attributes()["x-tvg-url"] = "newvalue"
        self.assertNotEqual(pl, new_pl)

    def test_group_by_attribute(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        groups = pl.group_by_attribute(IPTVAttr.GROUP_TITLE)
        diff = DeepDiff(groups, test_data.expected_m3u_plus_group_by_group_title, ignore_order=True)
        self.assertEqual(0, len(diff))

    def test_group_by_attribute_with_no_group_enabled(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        empty_group_channel = IPTVChannel(
            url="http://emptygroup.channel/mychannel", attributes={IPTVAttr.GROUP_TITLE: ""}
        )
        no_group_channel = IPTVChannel(url="http://nogroup.channel/mychannel", attributes={IPTVAttr.TVG_ID: "someid"})
        pl.append_channel(empty_group_channel)
        pl.append_channel(no_group_channel)
        groups = pl.group_by_attribute(IPTVAttr.GROUP_TITLE)
        expected_groups = test_data.expected_m3u_plus_group_by_group_title.copy()
        expected_groups[M3UPlaylist.NO_GROUP_KEY] = [4, 5]
        diff = DeepDiff(groups, expected_groups, ignore_order=True)
        self.assertEqual(0, len(diff))

    def test_group_by_attribute_with_no_group_disabled(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        empty_group_channel = IPTVChannel(
            url="http://emptygroup.channel/mychannel", attributes={IPTVAttr.GROUP_TITLE: ""}
        )
        no_group_channel = IPTVChannel(url="http://nogroup.channel/mychannel", attributes={IPTVAttr.TVG_ID: "someid"})
        pl.append_channel(empty_group_channel)
        pl.append_channel(no_group_channel)
        groups = pl.group_by_attribute(IPTVAttr.GROUP_TITLE, include_no_group=False)
        diff = DeepDiff(groups, test_data.expected_m3u_plus_group_by_group_title, ignore_order=True)
        self.assertEqual(0, len(diff))

    def test_group_by_url_with_no_group_disabled(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        groups = pl.group_by_url(include_no_group=False)
        diff = DeepDiff(groups, test_data.expected_m3u_plus_group_by_url, ignore_order=True)
        self.assertEqual(0, len(diff))

    def test_group_by_url_with_no_group_enabled(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        first_empty_url_channel = IPTVChannel(url="", attributes={IPTVAttr.GROUP_TITLE: "first"})
        second_empty_url_channel = IPTVChannel(url="", attributes={IPTVAttr.GROUP_TITLE: "second"})
        pl.append_channel(first_empty_url_channel)
        pl.append_channel(second_empty_url_channel)
        groups = pl.group_by_url(include_no_group=True)
        expected_groups = test_data.expected_m3u_plus_group_by_url.copy()
        expected_groups[M3UPlaylist.NO_URL_KEY] = [4, 5]
        diff = DeepDiff(groups, expected_groups, ignore_order=True)
        self.assertEqual(0, len(diff))

    def test_match_single(self):
        ch = test_data.m3u_plus_channel_0
        result = M3UPlaylist._match_single(ch, re.compile(".*Rai.*"), where="attributes.tvg-name")
        self.assertTrue(result)
        result = M3UPlaylist._match_single(ch, re.compile(".*rai.*"), where="attributes.tvg-name")
        self.assertFalse(result)
        result = M3UPlaylist._match_single(ch, re.compile(".*rai.*", re.IGNORECASE), where="attributes.tvg-name")
        self.assertTrue(result)
        result = M3UPlaylist._match_single(ch, re.compile(".*Music.*"), where="duration")
        self.assertFalse(result)
        result = M3UPlaylist._match_single(ch, re.compile(".*luke.*"), where="url")
        self.assertTrue(result)
        result = M3UPlaylist._match_single(ch, re.compile(".*luke.*"), where="non-existent")
        self.assertFalse(result)
        result = M3UPlaylist._match_single(ch, re.compile(".*luke.*"), where="attributes.non-existent")
        self.assertFalse(result)
        result = M3UPlaylist._match_single(ch, re.compile(".*luke.*"), where="non-existent.tvg-name")
        self.assertFalse(result)

    def test_match_all(self):
        ch = test_data.m3u_plus_channel_0
        result = M3UPlaylist._match_all(ch, re.compile(".*RAI.*"))
        self.assertTrue(result)
        result = M3UPlaylist._match_all(ch, re.compile(".*rai 1.*", re.IGNORECASE))
        self.assertTrue(result)
        result = M3UPlaylist._match_all(ch, re.compile(".*music.*", re.IGNORECASE))
        self.assertFalse(result)
        result = M3UPlaylist._match_all(ch, re.compile("^-1$"))
        self.assertTrue(result)
        result = M3UPlaylist._match_all(ch, re.compile(".*luke.*"))
        self.assertTrue(result)

    def test_search_by_list_index(self):
        pl = M3UPlaylist()
        pl.append_channels(
            [IPTVChannel(name="a", extras=["#EXTVLCOPT:x=1"]), IPTVChannel(name="b", extras=["#EXTGRP:news"])]
        )
        results = pl.search("#EXTGRP:.*", where="extras.0")
        self.assertEqual(["b"], [ch.name for ch in results])

    def test_search(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        results = pl.search(".*luke.*")
        self.assertEqual(4, len(results))
        results = pl.search(".*Italia.*", where="attributes.group-title")
        self.assertEqual(2, len(results))
        results = pl.search(".*TROISI.*", where="name")
        self.assertEqual(1, len(results))
        results = pl.search(".*R.*", where="name")
        self.assertEqual(3, len(results))
        # Search for empty tvg-id attribute
        results = pl.search("^$", where="attributes.tvg-id")
        self.assertEqual(2, len(results))
        # Search for any empty attribute
        results = pl.search("^$")
        self.assertEqual(3, len(results))
        # Search in a set of attributes
        results = pl.search(".*it.*", where=["attributes.tvg-logo", "attributes.group-title"], case_sensitive=False)
        self.assertEqual(3, len(results))
        # Check that no duplicates are added
        results = pl.search(
            ".*RAI.*",
            where=["attributes.tvg-id", "attributes.tvg-name", "attributes.tvg-logo", "attributes.group-title", "name"],
            case_sensitive=False,
        )
        self.assertEqual(1, len(results))

    def test_parse_header(self):
        # Case of a header with no attributes
        header = "#EXTM3U"
        attributes = playlist._parse_header(header)
        self.assertEqual(0, len(attributes))

        # Case of a header with attributes
        header = '#EXTM3U x-tvg-url="https://elcinema.com.epg.xml" tvg-shift="1"'
        attributes = playlist._parse_header(header)
        self.assertEqual(attributes["x-tvg-url"], "https://elcinema.com.epg.xml")
        self.assertEqual(attributes["tvg-shift"], "1")

    def test_parse_header_with_special_values(self):
        # Attribute values may contain spaces and "=" characters and must
        # not be truncated.
        header = '#EXTM3U url-tvg="a b c" x-tvg-url="http://e.com/g.xml?a=1&b=2" tvg-shift="0"'
        attributes = playlist._parse_header(header)
        self.assertEqual(attributes["url-tvg"], "a b c")
        self.assertEqual(attributes["x-tvg-url"], "http://e.com/g.xml?a=1&b=2")
        self.assertEqual(attributes["tvg-shift"], "0")

    def test_build_header(self):
        expected_header = '#EXTM3U x-tvg-url="https://elcinema.com.epg.xml" tvg-shift="1"'
        pl = M3UPlaylist()
        pl.add_attributes(playlist._parse_header(expected_header))
        self.assertEqual(expected_header, pl._build_header())

    def test_iterator(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        for i, ch in enumerate(pl):
            self.assertEqual(test_data.expected_m3u_plus.get_channel(i), ch)
        self.assertEqual(i + 1, test_data.expected_m3u_plus.length())

    def test_nested_iteration(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        length = pl.length()
        pairs = [(outer, inner) for outer in pl for inner in pl]
        self.assertEqual(length * length, len(pairs))

    def test_get_channel(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        ch = pl.get_channel(2)
        # Success case
        self.assertEqual(ch, test_data.m3u_plus_channel_2)
        # Failure case
        self.assertRaises(IndexOutOfBoundsException, pl.get_channel, pl.length())
        self.assertRaises(IndexOutOfBoundsException, pl.get_channel, -pl.length() - 1)

    def test_get_channel_with_negative_index(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        self.assertIs(pl.get_channels()[-1], pl.get_channel(-1))
        self.assertIs(pl.get_channels()[0], pl.get_channel(-pl.length()))

    def test_append_channel(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        new_channel = IPTVChannel(url="http://127.0.0.1", name="new channel", duration="-1")
        pl2.append_channel(new_channel)
        self.assertEqual(new_channel, pl2.get_channel(pl2.length() - 1))
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl1.length() + 1, pl2.length())

    def test_append_channels(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        # Let's append the same channels twice
        pl2.append_channels(pl1.get_channels())
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl1.length() * 2, pl2.length())
        self.assertEqual(pl1.get_channels(), pl2.get_channels()[: pl1.length()])
        self.assertEqual(pl1.get_channels(), pl2.get_channels()[pl1.length() :])

    def test_insert_channel(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        new_channel = IPTVChannel(url="http://127.0.0.1", name="new channel", duration="-1")
        inserted_index = 2
        pl2.insert_channel(inserted_index, new_channel)
        self.assertEqual(new_channel, pl2.get_channel(inserted_index))
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl1.length() + 1, pl2.length())
        self.assertEqual(pl1.get_channels()[:inserted_index], pl2.get_channels()[:inserted_index])
        self.assertEqual(pl1.get_channels()[inserted_index:], pl2.get_channels()[inserted_index + 1 :])
        # Failure cases
        self.assertRaises(IndexOutOfBoundsException, pl2.insert_channel, pl2.length() + 1, new_channel)
        self.assertRaises(IndexOutOfBoundsException, pl2.insert_channel, -pl2.length() - 1, new_channel)

    def test_insert_channel_with_negative_index(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        new_channel = IPTVChannel(url="http://127.0.0.1", name="new channel")
        pl2.insert_channel(-1, new_channel)
        expected = pl1.get_channels()
        expected.insert(-1, new_channel)
        self.assertEqual(expected, pl2.get_channels())

    def test_insert_channels_with_negative_index(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        pl2.insert_channels(-1, pl1.get_channels())
        self.assertEqual(pl1.get_channels()[:-1] + pl1.get_channels() + pl1.get_channels()[-1:], pl2.get_channels())

    def test_insert_channel_at_end(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        new_channel = IPTVChannel(url="http://127.0.0.1", name="new channel")
        pl.insert_channel(pl.length(), new_channel)
        self.assertEqual(new_channel, pl.get_channels()[-1])

    def test_insert_channel_in_empty_playlist(self):
        pl = M3UPlaylist()
        new_channel = IPTVChannel(url="http://127.0.0.1", name="new channel")
        pl.insert_channel(0, new_channel)
        self.assertEqual([new_channel], pl.get_channels())

    def test_insert_channels(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        # Let's insert pl1 channels at a specific offset in pl2
        offset = 2
        pl2.insert_channels(offset, pl1.get_channels())
        self.assertNotEqual(pl1, pl2)
        for i in range(pl1.length()):
            self.assertEqual(pl1.get_channel(i), pl2.get_channel(offset + i))
        # Failure case
        self.assertRaises(IndexOutOfBoundsException, pl2.insert_channels, pl2.length() + 1, pl1.get_channels())

    def test_insert_channels_at_end(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        pl2.insert_channels(pl2.length(), pl1.get_channels())
        self.assertEqual(pl1.get_channels() * 2, pl2.get_channels())

    def test_len(self):
        self.assertEqual(0, len(M3UPlaylist()))
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        self.assertEqual(pl.length(), len(pl))

    def test_getitem(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        self.assertIs(pl.get_channel(1), pl[1])
        self.assertIs(pl.get_channel(pl.length() - 1), pl[-1])
        with self.assertRaises(IndexOutOfBoundsException):
            pl[pl.length()]
        with self.assertRaises(IndexOutOfBoundsException):
            pl[-pl.length() - 1]

    def test_out_of_bounds_index_is_an_index_error(self):
        pl = M3UPlaylist()
        with self.assertRaises(IndexError):
            pl[0]
        with self.assertRaises(IPyTVException):
            pl[0]

    def test_eq(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        pl2.add_attribute("x-new", "value")
        self.assertNotEqual(pl1, pl2)
        pl3 = pl1.copy()
        pl3[0] = IPTVChannel(name="other")
        self.assertNotEqual(pl1, pl3)
        self.assertNotEqual(pl1, pl1.get_channels())
        self.assertNotEqual(pl1, None)

    def test_setitem(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        new_channel = IPTVChannel(url="http://127.0.0.1", name="new channel")
        pl[1] = new_channel
        self.assertIs(new_channel, pl.get_channel(1))
        pl[-1] = new_channel
        self.assertIs(new_channel, pl.get_channel(pl.length() - 1))
        with self.assertRaises(IndexOutOfBoundsException):
            pl[pl.length()] = new_channel

    def test_delitem(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        del pl2[1]
        self.assertEqual(pl1.get_channels()[:1] + pl1.get_channels()[2:], pl2.get_channels())
        del pl2[-1]
        self.assertEqual(pl1.get_channels()[:1] + pl1.get_channels()[2:-1], pl2.get_channels())
        with self.assertRaises(IndexOutOfBoundsException):
            del pl2[pl2.length()]

    def test_repr(self):
        pl = M3UPlaylist()
        pl.add_attribute("x-tvg-url", "http://example.com/epg.xml")
        pl.append_channel(IPTVChannel(name="News"))
        self.assertEqual("<M3UPlaylist channels=1 attributes={'x-tvg-url': 'http://example.com/epg.xml'}>", repr(pl))

    def test_copy_module(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl_copy = copy.copy(pl)
        self.assertEqual(pl, pl_copy)
        self.assertIsNot(pl.get_channel(0), pl_copy.get_channel(0))

    def test_update_channel(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        updated_index = 3
        new_channel = IPTVChannel(url="http://127.0.0.1", name="new channel", duration="-1")
        pl2.update_channel(updated_index, new_channel)
        self.assertNotEqual(pl1, pl2)
        for i, ch in enumerate(pl1):
            if i == updated_index:
                self.assertNotEqual(ch, pl2.get_channel(i))
            else:
                self.assertEqual(ch, pl2.get_channel(i))
        # Failure case
        self.assertRaises(IndexOutOfBoundsException, pl2.update_channel, pl2.length(), new_channel)
        self.assertRaises(IndexOutOfBoundsException, pl2.update_channel, -pl2.length() - 1, new_channel)

    def test_update_channel_with_negative_index(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        new_channel = IPTVChannel(url="http://127.0.0.1", name="new channel")
        pl.update_channel(-1, new_channel)
        self.assertIs(new_channel, pl.get_channels()[-1])

    def test_remove_channel(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        expected_length = test_data.expected_m3u_plus.length()
        removed_index = 0
        self.assertEqual(expected_length, pl.length())
        channel = pl.remove_channel(removed_index)
        self.assertEqual(test_data.expected_m3u_plus.get_channel(removed_index), channel)
        self.assertEqual(expected_length - 1, pl.length())
        # Failure case
        self.assertRaises(IndexOutOfBoundsException, pl.remove_channel, pl.length())
        self.assertRaises(IndexOutOfBoundsException, pl.remove_channel, -pl.length() - 1)

    def test_remove_channel_with_negative_index(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1.get_channels()[-1], pl2.remove_channel(-1))
        self.assertEqual(pl1.get_channels()[:-1], pl2.get_channels())

    def test_get_attribute(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        name = "x-tvg-url"
        value = pl.get_attribute(name)
        self.assertEqual(test_data.expected_m3u_plus.get_attributes()[name], value)

    def test_add_attribute(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        name = "test-attribute"
        value = "test-value"
        pl2.add_attribute(name, value)
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl2.get_attributes()[name], value)
        self.assertEqual(len(test_data.expected_m3u_plus.get_attributes()) + 1, len(pl2.get_attributes()))
        # Failure case
        self.assertRaises(AttributeAlreadyPresentException, pl2.add_attribute, name, value)

    def test_add_attributes(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        new_attributes = {"attribute_1": "value_1", "attribute_2": "value_2"}
        pl2.add_attributes(new_attributes)
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl2.get_attributes()["attribute_2"], "value_2")
        self.assertEqual(
            len(test_data.expected_m3u_plus.get_attributes()) + len(new_attributes), len(pl2.get_attributes())
        )
        # Failure case
        self.assertRaises(AttributeAlreadyPresentException, pl2.add_attribute, "attribute_2", "value_2")

    def test_update_attribute(self):
        pl1 = playlist.loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        updated_attribute = "x-tvg-url"
        new_value = "new-value"
        pl2.update_attribute(updated_attribute, new_value)
        self.assertNotEqual(pl1, pl2)
        self.assertNotEqual(pl1.get_attribute(updated_attribute), pl2.get_attribute(updated_attribute))
        # Failure case
        self.assertRaises(AttributeNotFoundException, pl2.update_attribute, "non-existing-attribute", "value")

    def test_remove_attribute(self):
        pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        expected_length = len(test_data.expected_m3u_plus.get_attributes())
        self.assertEqual(expected_length, len(pl.get_attributes()))
        removed_attribute = "x-tvg-url"
        attribute = pl.remove_attribute(removed_attribute)
        self.assertEqual(test_data.expected_m3u_plus.get_attribute(removed_attribute), attribute)
        self.assertEqual(expected_length - 1, len(pl.get_attributes()))
        # Failure case
        self.assertRaises(AttributeNotFoundException, pl.remove_attribute, "non-existing-attribute")


if __name__ == "__main__":
    unittest.main()
