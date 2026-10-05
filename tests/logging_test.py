import logging
import unittest
from unittest import mock

import ipytv.channel
import ipytv.playlist as playlist
from ipytv.channel import IPTVChannel
from ipytv.exceptions import IPyTVException
from ipytv.playlist import M3UPlaylist
from tests.playlist_test import produce_triples


def _m3u_plus_body() -> list[str]:
    with open("tests/resources/m3u_plus.m3u", encoding="utf-8") as file:
        return file.readlines()[1:]


class TestLogging(unittest.TestCase):
    def test_single_null_handler_on_the_package_logger(self):
        handlers = logging.getLogger("ipytv").handlers
        self.assertTrue(any(isinstance(h, logging.NullHandler) for h in handlers))
        for name in ("ipytv.playlist", "ipytv.channel", "ipytv.doctor"):
            self.assertEqual([], logging.getLogger(name).handlers, name)

    def test_parsing_logs_nothing_at_info(self):
        with self.assertNoLogs("ipytv", level="INFO"):
            playlist._populate(_m3u_plus_body())
            playlist.loadl(["#EXTM3U", '#EXTINF:-1 tvg-id="1",Channel', "http://example.com/1"])

    def test_mutations_log_nothing_at_info(self):
        with self.assertNoLogs("ipytv", level="INFO"):
            pl = M3UPlaylist()
            pl.append_channel(IPTVChannel(url="http://example.com/1"))
            pl.append_channels([IPTVChannel(url="http://example.com/2")])
            pl.insert_channel(0, IPTVChannel(url="http://example.com/0"))
            pl.insert_channels(0, [IPTVChannel(url="http://example.com/-1")])
            pl.update_channel(0, IPTVChannel(url="http://example.com/x"))
            pl.remove_channel(0)
            pl.add_attribute("a", "1")
            pl.add_attributes({"b": "2"})
            pl.update_attribute("a", "3")
            pl.remove_attribute("a")

    def test_raised_errors_are_not_also_logged(self):
        with_attribute = M3UPlaylist()
        with_attribute.add_attribute("a", "1")
        failing_calls = [
            lambda: M3UPlaylist()[0],
            lambda: M3UPlaylist().update_attribute("missing", "1"),
            lambda: M3UPlaylist().remove_attribute("missing"),
            lambda: with_attribute.add_attribute("a", "2"),
            lambda: playlist.loadl("not a list"),
            lambda: playlist.loadl([]),
            lambda: playlist.loadl(["not a header"]),
            lambda: playlist.loads(42),
            lambda: playlist.loadf(42),
            lambda: playlist.loadu(42),
            lambda: playlist.loadj("not a dict"),
            lambda: playlist.loadjstr(42),
            lambda: playlist.loadjstr("{not json"),
            lambda: IPTVChannel().parse_extinf_string("#EXTINF :-1,Channel"),
        ]
        for i, call in enumerate(failing_calls):
            with self.subTest(i=i), self.assertNoLogs("ipytv", level="ERROR"), self.assertRaises(IPyTVException):
                call()

    def test_unparsable_extinf_row_warns_that_the_channel_is_kept(self):
        with self.assertLogs("ipytv", level="WARNING") as logs:
            channel = ipytv.channel.from_playlist_entry(["#EXTINF :-1,Channel", "http://example.com/1"])
        self.assertEqual("http://example.com/1", channel.url)
        self.assertIn("kept with its URL", logs.output[0])

    def test_disabled_debug_logging_is_not_called_per_row(self):
        package_logger = logging.getLogger("ipytv")
        previous_level = package_logger.level
        package_logger.setLevel(logging.WARNING)
        self.addCleanup(package_logger.setLevel, previous_level)
        body = produce_triples(1000)
        with (
            mock.patch.object(playlist.log, "debug") as playlist_debug,
            mock.patch.object(ipytv.channel.log, "debug") as channel_debug,
        ):
            playlist._populate(body)
        self.assertLess(playlist_debug.call_count, 5)
        self.assertLess(channel_debug.call_count, 5)

    def test_enabled_debug_logging_reports_each_row(self):
        body = produce_triples(3)
        with self.assertLogs("ipytv.playlist", level="DEBUG") as logs:
            playlist._populate(body)
        parsed_rows = [line for line in logs.output if "parsing row" in line]
        self.assertEqual(len(body) - 1, len(parsed_rows))


if __name__ == "__main__":
    unittest.main()
