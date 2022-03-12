import unittest

import httpretty
import m3u8
from deepdiff import DeepDiff

from ipytv.channel import IPTVAttr, IPTVChannel
from ipytv.exceptions import IndexOutOfBoundsException, AttributeAlreadyPresentException, AttributeNotFoundException
from ipytv.playlist import M3UPlaylist
from tests import test_data


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
        self.assertEqual(expected_length, pl2.length(), "The size of the playlist is not the expected one")


class TestLoadfM3UPlus(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        self.assertTrue(pl == test_data.expected_m3u_plus, "The two playlists are not equal")


class TestLoadfM3U8(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u8.m3u")
        self.assertEqual(test_data.expected_m3u8, pl, "The two playlists are not equal")


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
        # The rstrip() method invocation is needed because the dumps() method of
        # the m3u8 library adds a (redundant?) final newline character that this
        # library doesn't add.
        self.assertEqual(pl_string, pl_m3u8_string.rstrip())


class TestClone(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist.loadf("tests/resources/m3u_plus.m3u")
        new_pl = pl.copy()
        new_pl.append_channel(
            IPTVChannel(name="mynewchannel", url="mynewurl")
        )
        self.assertEqual(pl.length()+1, new_pl.length())
        current_name: str = new_pl.get_channel(0).name
        new_pl.get_channel(0).name = "my " + current_name
        self.assertTrue(pl.get_channel(0).name != new_pl.get_channel(0).name)


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
        pl.append_channel(empty_group_channel)
        pl.append_channel(no_group_channel)
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
        pl.append_channel(empty_group_channel)
        pl.append_channel(no_group_channel)
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
        pl.append_channel(first_empty_url_channel)
        pl.append_channel(second_empty_url_channel)
        groups = pl.group_by_url(include_no_group=True)
        expected_groups = test_data.expected_m3u_plus_group_by_url.copy()
        expected_groups[M3UPlaylist.NO_URL_KEY] = [4, 5]
        diff = DeepDiff(groups, expected_groups, ignore_order=True)
        self.assertTrue(len(diff) == 0)


class TestParseHeader(unittest.TestCase):
    def runTest(self):
        header = '#EXTM3U x-tvg-url="https://elcinema.com.epg.xml" tvg-shift="1"'
        pl = M3UPlaylist()
        pl.parse_header(header)
        self.assertEqual(pl.get_attributes()['x-tvg-url'], 'https://elcinema.com.epg.xml')
        self.assertEqual(pl.get_attributes()['tvg-shift'], '1')


class TestBuildHeader(unittest.TestCase):
    def runTest(self):
        expected_header = '#EXTM3U x-tvg-url="https://elcinema.com.epg.xml" tvg-shift="1"'
        pl = M3UPlaylist()
        pl.parse_header(expected_header)
        self.assertEqual(expected_header, pl.build_header())


class TestIterator(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        for i, ch in enumerate(pl):
            self.assertEqual(test_data.expected_m3u_plus.get_channel(i), ch)
        self.assertEqual(i+1, test_data.expected_m3u_plus.length())


class TestGetChannel(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        ch = pl.get_channel(2)
        # Success case
        self.assertEqual(ch, test_data.m3u_plus_channel_2)
        # Failure case
        self.assertRaises(IndexOutOfBoundsException, pl.get_channel, pl.length())


class TestAppendChannel(unittest.TestCase):
    def runTest(self):
        pl1 = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        new_channel = IPTVChannel(
            url="http://127.0.0.1",
            name="new channel",
            duration="-1"
        )
        pl2.append_channel(new_channel)
        self.assertEqual(new_channel, pl2.get_channel(pl2.length()-1))
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl1.length()+1, pl2.length())


class TestAppendChannels(unittest.TestCase):
    def runTest(self):
        pl1 = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        # Let's append the same channels twice
        pl2.append_channels(pl1.get_channels())
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl1.length()*2, pl2.length())
        self.assertEqual(pl1.get_channels(), pl2.get_channels()[:pl1.length()])
        self.assertEqual(pl1.get_channels(), pl2.get_channels()[pl1.length():])


class TestInsertChannel(unittest.TestCase):
    def runTest(self):
        pl1 = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        new_channel = IPTVChannel(
            url="http://127.0.0.1",
            name="new channel",
            duration="-1"
        )
        inserted_index = 2
        pl2.insert_channel(inserted_index, new_channel)
        self.assertEqual(new_channel, pl2.get_channel(inserted_index))
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl1.length()+1, pl2.length())
        self.assertEqual(pl1.get_channels()[:inserted_index], pl2.get_channels()[:inserted_index])
        self.assertEqual(pl1.get_channels()[inserted_index:], pl2.get_channels()[inserted_index+1:])
        # Failure case
        self.assertRaises(IndexOutOfBoundsException, pl2.insert_channel, pl2.length(), new_channel)


class TestInsertChannels(unittest.TestCase):
    def runTest(self):
        pl1 = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        # Let's append the same channels twice
        pl2.append_channels(pl1.get_channels())
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl1.length()*2, pl2.length())
        self.assertEqual(pl1.get_channels(), pl2.get_channels()[:pl1.length()])
        self.assertEqual(pl1.get_channels(), pl2.get_channels()[pl1.length():])
        # Failure case
        self.assertRaises(IndexOutOfBoundsException, pl2.insert_channels, pl2.length(), pl1.get_channels())


class TestUpdateChannel(unittest.TestCase):
    def runTest(self):
        pl1 = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        updated_index = 3
        new_channel = IPTVChannel(
            url="http://127.0.0.1",
            name="new channel",
            duration="-1"
        )
        pl2.update_channel(updated_index, new_channel)
        self.assertNotEqual(pl1, pl2)
        for i, ch in enumerate(pl1):
            if i == updated_index:
                self.assertNotEqual(ch, pl2.get_channel(i))
            else:
                self.assertEqual(ch, pl2.get_channel(i))
        # Failure case
        self.assertRaises(
            IndexOutOfBoundsException,
            pl2.update_channel,
            pl2.length(),
            new_channel
        )


class TestRemoveChannel(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        expected_length = test_data.expected_m3u_plus.length()
        removed_index = 0
        self.assertEqual(expected_length, pl.length())
        channel = pl.remove_channel(removed_index)
        self.assertEqual(test_data.expected_m3u_plus.get_channel(removed_index), channel)
        self.assertEqual(expected_length-1, pl.length())
        # Failure case
        self.assertRaises(IndexOutOfBoundsException, pl.remove_channel, pl.length())


class TestGetAttribute(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        name = "x-tvg-url"
        value = pl.get_attribute(name)
        self.assertEqual(test_data.expected_m3u_plus.get_attributes()[name], value)


class TestAddAttribute(unittest.TestCase):
    def runTest(self):
        pl1 = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        name = 'test-attribute'
        value = 'test-value'
        pl2.add_attribute(name, value)
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl2.get_attributes()[name], value)
        self.assertEqual(
            len(test_data.expected_m3u_plus.get_attributes()) + 1,
            len(pl2.get_attributes())
        )
        # Failure case
        self.assertRaises(
            AttributeAlreadyPresentException,
            pl2.add_attribute,
            name,
            value
        )


class TestAddAttributes(unittest.TestCase):
    def runTest(self):
        pl1 = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        new_attributes = {
            "attribute_1": "value_1",
            "attribute_2": "value_2"
        }
        pl2.add_attributes(new_attributes)
        self.assertNotEqual(pl1, pl2)
        self.assertEqual(pl2.get_attributes()["attribute_2"], "value_2")
        self.assertEqual(
            len(test_data.expected_m3u_plus.get_attributes()) + len(new_attributes),
            len(pl2.get_attributes())
        )
        # Failure case
        self.assertRaises(
            AttributeAlreadyPresentException,
            pl2.add_attribute,
            "attribute_2",
            "value_2"
        )


class TestUpdateAttribute(unittest.TestCase):
    def runTest(self):
        pl1 = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        pl2 = pl1.copy()
        self.assertEqual(pl1, pl2)
        updated_attribute = "x-tvg-url"
        new_value = "new-value"
        pl2.update_attribute(updated_attribute, new_value)
        self.assertNotEqual(pl1, pl2)
        self.assertNotEqual(pl1.get_attribute(updated_attribute), pl2.get_attribute(updated_attribute))
        # Failure case
        self.assertRaises(
            AttributeNotFoundException,
            pl2.update_attribute,
            "non-existing-attribute",
            "value"
        )


class TestRemoveAttribute(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist().loadf("tests/resources/m3u_plus.m3u")
        expected_length = len(test_data.expected_m3u_plus.get_attributes())
        self.assertEqual(expected_length, len(pl.get_attributes()))
        removed_attribute = "x-tvg-url"
        attribute = pl.remove_attribute(removed_attribute)
        self.assertEqual(test_data.expected_m3u_plus.get_attribute(removed_attribute), attribute)
        self.assertEqual(expected_length - 1, len(pl.get_attributes()))
        # Failure case
        self.assertRaises(
            AttributeNotFoundException,
            pl.remove_attribute,
            "non-existing-attribute"
        )


if __name__ == '__main__':
    unittest.main()
