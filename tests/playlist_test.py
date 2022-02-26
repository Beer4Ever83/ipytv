import logging
import unittest

import httpretty
import m3u8
from deepdiff import DeepDiff

from ipytv import IPTVAttr, IPTVChannel, M3UPlaylist
from tests import test_data

logging.basicConfig(level=logging.DEBUG)


class TestChunkArray0(unittest.TestCase):
    def runTest(self):
        body = []
        for i in range(0, 97):
            body.append(i)
        chunks = M3UPlaylist.chunk_array(body, 4)
        self.assertEqual(4, len(chunks))
        self.assertEqual({"begin": 0, "end": 25}, chunks[0])
        self.assertEqual({"begin": 24, "end": 49}, chunks[1])
        self.assertEqual({"begin": 48, "end": 73}, chunks[2])
        self.assertEqual({"begin": 72, "end": 97}, chunks[3])


class TestChunkArray1(unittest.TestCase):
    def runTest(self):
        body = []
        for i in range(0, 98):
            body.append(i)
        chunks = M3UPlaylist.chunk_array(body, 4)
        self.assertEqual(4, len(chunks))
        self.assertEqual({"begin": 0, "end": 25}, chunks[0])
        self.assertEqual({"begin": 24, "end": 49}, chunks[1])
        self.assertEqual({"begin": 48, "end": 73}, chunks[2])
        self.assertEqual({"begin": 72, "end": 98}, chunks[3])


class TestChunkArray2(unittest.TestCase):
    def runTest(self):
        body = []
        for i in range(0, 99):
            body.append(i)
        chunks = M3UPlaylist.chunk_array(body, 4)
        self.assertEqual(4, len(chunks))
        self.assertEqual({"begin": 0, "end": 25}, chunks[0])
        self.assertEqual({"begin": 24, "end": 49}, chunks[1])
        self.assertEqual({"begin": 48, "end": 73}, chunks[2])
        self.assertEqual({"begin": 72, "end": 99}, chunks[3])


class TestChunkArray3(unittest.TestCase):
    def runTest(self):
        body = []
        for i in range(0, 100):
            body.append(i)
        chunks = M3UPlaylist.chunk_array(body, 4)
        self.assertEqual(4, len(chunks))
        self.assertEqual({"begin": 0, "end": 26}, chunks[0])
        self.assertEqual({"begin": 25, "end": 51}, chunks[1])
        self.assertEqual({"begin": 50, "end": 76}, chunks[2])
        self.assertEqual({"begin": 75, "end": 100}, chunks[3])


class TestLoadaM3UPlusHuge(unittest.TestCase):
    def runTest(self):
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
        pl2 = M3UPlaylist.loada(new_buffer)
        self.assertEqual(expected_length, len(pl2.list), "The size of the playlist is not the expected one")


class TestLoadfM3UPlus(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        self.assertTrue(pl == test_data.expected_m3u_plus, "The two playlists are not equal")


class TestLoadfM3U8(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u8.m3u")
        self.assertTrue(pl == test_data.expected_m3u8, "The two playlists are not equal")


class TestLoaduM3UPlus(unittest.TestCase):
    def runTest(self):
        url = "http://myown.link:80/luke/playlist.m3u"
        with open("tests/resources/m3u_plus.m3u") as content:
            body = "".join(content.readlines())
        with httpretty.enabled():
            httpretty.register_uri(
                httpretty.GET,
                url,
                adding_headers={"Content-Type": "application/octet-stream"},
                body=body,
                status=200
            )
            pl = M3UPlaylist.loadu(url)
        httpretty.disable()
        httpretty.reset()
        self.assertTrue(pl == test_data.expected_m3u_plus, "The two playlists are not equal")


class TestLoaduM3U8(unittest.TestCase):
    def runTest(self):
        url = "http://myown.link:80/luke/playlist.m3u"
        with open("tests/resources/m3u8.m3u", encoding="utf-8") as content:
            body = "".join(content.readlines())
        with httpretty.enabled():
            httpretty.register_uri(
                httpretty.GET,
                url,
                adding_headers={"Content-Type": "application/octet-stream"},
                body=body,
                status=200
            )
            pl = M3UPlaylist.loadu(url)
        httpretty.disable()
        httpretty.reset()
        self.assertTrue(pl == test_data.expected_m3u8, "The two playlists are not equal")


class TestLoaduErrors(unittest.TestCase):
    def runTest(self):
        # For some reason the error 421 is not recognized by httpretty so it has been removed from the list
        error_codes = ["400", "401", "402", "403", "404", "405", "406", "407", "408", "409",
                       "410", "411", "412", "413", "414", "415", "416", "417", "418",
                       "422", "423", "424", "425", "426", "428", "429", "431", "451", "500",
                       "501", "502", "503", "504", "505", "506", "507", "508", "510", "511"]
        url = "http://myown.link:80/luke/playlist.m3u"
        with httpretty.enabled():
            for code in error_codes:
                httpretty.register_uri(
                    httpretty.GET,
                    url,
                    status=code
                )
                self.assertRaises(Exception, M3UPlaylist.loadu, url)
        httpretty.disable()
        httpretty.reset()


class TestToM3UPlusPlaylist(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        with open("tests/resources/m3u_plus.m3u") as file:
            expected_content = "".join(file.readlines())
            content = pl.to_m3u_plus_playlist()
            self.assertTrue(content == expected_content, "The two playlists are not equal")


class TestToM3U8Playlist(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        pl_string = pl.to_m3u8_playlist()
        pl_m3u8 = m3u8.loads(pl_string)
        pl_m3u8_string = pl_m3u8.dumps()
        self.assertTrue(pl_string == pl_m3u8_string)


class TestClone(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        newpl = pl.copy()
        newpl.add_channel(
            IPTVChannel(name="mynewchannel", url="mynewurl")
        )
        self.assertTrue(len(pl.list)+1 == len(newpl.list))
        newpl.list[0].name = "my " + newpl.list[0].name
        self.assertTrue(pl.list[0].name != newpl.list[0].name)


class TestGroupByAttribute(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        groups = pl.group_by_attribute(IPTVAttr.GROUP_TITLE.value)
        diff = DeepDiff(groups, test_data.expected_m3u_plus_group_by_group_title, ignore_order=True)
        self.assertTrue(len(diff) == 0)


class TestGroupByAttributeWithNoGroupEnabled(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        empty_group_channel = IPTVChannel(
            url="http://emptygroup.channel/mychannel",
            attributes={
                IPTVAttr.GROUP_TITLE.value: ""
            }
        )
        no_group_channel = IPTVChannel(
            url="http://nogroup.channel/mychannel",
            attributes={
                IPTVAttr.TVG_ID.value: "someid"
            }
        )
        pl.add_channel(empty_group_channel)
        pl.add_channel(no_group_channel)
        groups = pl.group_by_attribute(IPTVAttr.GROUP_TITLE.value)
        expected_groups = test_data.expected_m3u_plus_group_by_group_title.copy()
        expected_groups[M3UPlaylist.NO_GROUP_KEY] = [4, 5]
        diff = DeepDiff(groups, expected_groups, ignore_order=True)
        self.assertTrue(len(diff) == 0)


class TestGroupByAttributeWithNoGroupDisabled(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        empty_group_channel = IPTVChannel(
            url="http://emptygroup.channel/mychannel",
            attributes={
                IPTVAttr.GROUP_TITLE.value: ""
            }
        )
        no_group_channel = IPTVChannel(
            url="http://nogroup.channel/mychannel",
            attributes={
                IPTVAttr.TVG_ID.value: "someid"
            }
        )
        pl.add_channel(empty_group_channel)
        pl.add_channel(no_group_channel)
        groups = pl.group_by_attribute(IPTVAttr.GROUP_TITLE.value, include_no_group=False)
        diff = DeepDiff(groups, test_data.expected_m3u_plus_group_by_group_title, ignore_order=True)
        self.assertTrue(len(diff) == 0)


class TestGroupByUrlWithNoGroupDisabled(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        groups = pl.group_by_url(include_no_group=False)
        diff = DeepDiff(groups, test_data.expected_m3u_plus_group_by_url, ignore_order=True)
        self.assertTrue(len(diff) == 0)


class TestGroupByUrlWithNoGroupEnabled(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        first_empty_url_channel = IPTVChannel(
            url="",
            attributes={
                IPTVAttr.GROUP_TITLE.value: "first"
            }
        )
        second_empty_url_channel = IPTVChannel(
            url="",
            attributes={
                IPTVAttr.GROUP_TITLE.value: "second"
            }
        )
        pl.add_channel(first_empty_url_channel)
        pl.add_channel(second_empty_url_channel)
        groups = pl.group_by_url(include_no_group=True)
        expected_groups = test_data.expected_m3u_plus_group_by_url.copy()
        expected_groups[M3UPlaylist.NO_URL_KEY] = [4, 5]
        diff = DeepDiff(groups, expected_groups, ignore_order=True)
        self.assertTrue(len(diff) == 0)


if __name__ == '__main__':
    unittest.main()
