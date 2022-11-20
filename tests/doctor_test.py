import unittest

from tests import test_data
from ipytv import playlist
from ipytv.channel import IPTVChannel, IPTVAttr
from ipytv.doctor import M3UDoctor, IPTVChannelDoctor, M3UPlaylistDoctor
from ipytv.playlist import M3UPlaylist


class TestFixSplitQuotedString(unittest.TestCase):
    def runTest(self):
        fixed = M3UDoctor.sanitize(test_data.split_quoted_string.split("\n"))
        self.assertEqual(test_data.expected_m3u_plus, playlist.loadl(fixed))


class TestFixUnquotedAttributes(unittest.TestCase):
    def runTest(self):
        fixed = M3UDoctor.sanitize(test_data.unquoted_attributes.split("\n"))
        self.assertEqual(test_data.expected_m3u_plus, playlist.loadl(fixed))


class TestURLEncodeLogo(unittest.TestCase):
    def runTest(self):
        extinf_string = """#EXTINF:-1 tvg-id="" tvg-name="" """ \
                        """tvg-logo="https://some.image.com/images/V1_UX182_CR0,0,182,268_AL_.jpg" """ \
                        """group-title="",My channel"""
        expected_attributes = {
            IPTVAttr.TVG_ID.value: "",
            IPTVAttr.TVG_NAME.value: "",
            IPTVAttr.TVG_LOGO.value: "https://some.image.com/images/V1_UX182_CR0%2C0%2C182%2C268_AL_.jpg",
            IPTVAttr.GROUP_TITLE.value: ""
        }
        expected = IPTVChannel(
            url="",
            name="My channel",
            duration="-1",
            attributes=expected_attributes
        )
        ch = IPTVChannel()
        ch.parse_extinf_string(extinf_string)
        IPTVChannelDoctor._urlencode_value(ch, IPTVAttr.TVG_LOGO.value)
        self.assertEqual(expected, ch, "the two channels are not equal")


class TestURLEncodeLogoNoChange(unittest.TestCase):
    def runTest(self):
        extinf_string = """#EXTINF:-1 tvg-id="" tvg-name="" tvg-language="Hindi" tvg-logo="https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcTZNoM8_ZqOG-8Lksy07YD-ltPehSFnfWcmxTU1LxlwbC58_8jcfJ987g" tvg-country="IN" tvg-url="" group-title="News",ABP Asmita"""
        expected_attributes = {
            IPTVAttr.TVG_ID.value: "",
            IPTVAttr.TVG_NAME.value: "",
            IPTVAttr.TVG_LANGUAGE.value: "Hindi",
            IPTVAttr.TVG_LOGO.value: "https://encrypted-tbn3.gstatic.com/images?q=tbn:ANd9GcTZNoM8_ZqOG-8Lksy07YD-ltPehSFnfWcmxTU1LxlwbC58_8jcfJ987g",
            IPTVAttr.TVG_COUNTRY.value: "IN",
            IPTVAttr.TVG_URL.value: "",
            IPTVAttr.GROUP_TITLE.value: "News"
        }
        expected = IPTVChannel(
            url="",
            name="ABP Asmita",
            duration="-1",
            attributes=expected_attributes
        )
        ch = IPTVChannel()
        ch.parse_extinf_string(extinf_string)
        IPTVChannelDoctor._urlencode_value(ch, IPTVAttr.TVG_LOGO.value)
        self.assertEqual(expected, ch, "the two channels are not equal")


class TestSanitizeAttributes(unittest.TestCase):
    def runTest(self):
        extinf_string = """#EXTINF:-1 tvg-ID="a" Tvg-name="contains, some,,commas" """ \
                """tvG-Logo="c" GROUP-TITLE="d",My channel"""
        expected_attributes = {
            IPTVAttr.TVG_ID.value: "a",
            IPTVAttr.TVG_NAME.value: "contains_ some__commas",
            IPTVAttr.TVG_LOGO.value: "c",
            IPTVAttr.GROUP_TITLE.value: "d"
        }
        expected = IPTVChannel(
            url="",
            name="My channel",
            duration="-1",
            attributes=expected_attributes
        )
        ch = IPTVChannel()
        ch.parse_extinf_string(extinf_string)
        new_ch = IPTVChannelDoctor.sanitize(ch)
        self.assertEqual(expected, new_ch, "the two channels are not equal")


class TestSanitizeURLEncodesAllLogos(unittest.TestCase):
    def runTest(self):
        pl = playlist.loadf("tests/resources/m3u_plus_unencoded_logo.m3u")
        self.assertNotEqual(test_data.expected_urlencoded, pl)
        fixed_pl = M3UPlaylistDoctor.sanitize(pl)
        self.assertEqual(test_data.expected_urlencoded, fixed_pl)


class TestSanitizeAllAttributes(unittest.TestCase):
    def runTest(self):
        pl = M3UPlaylist()
        pl.append_channel(
            IPTVChannel(attributes={"tvg-ID": "a"})
        )
        pl.append_channel(
            IPTVChannel(attributes={"TVG-LOGO": "b"})
        )
        pl.append_channel(
            IPTVChannel(attributes={"GrOuP-TiTlE": "c,d,,e"})
        )

        expected = M3UPlaylist()
        expected.append_channel(
            IPTVChannel(attributes={IPTVAttr.TVG_ID.value: "a"})
        )
        expected.append_channel(
            IPTVChannel(attributes={IPTVAttr.TVG_LOGO.value: "b"})
        )
        expected.append_channel(
            IPTVChannel(attributes={IPTVAttr.GROUP_TITLE.value: "c_d__e"})
        )
        self.assertNotEqual(expected, pl)
        fixed_pl = M3UPlaylistDoctor.sanitize(pl)
        self.assertEqual(expected, fixed_pl)


if __name__ == '__main__':
    unittest.main()
