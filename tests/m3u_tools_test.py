import unittest

import tests.test_data
from ipytv import M3UPlaylist
from ipytv.channel import IPTVChannel, IPTVAttr
from ipytv.m3u_tools import IPTVChannelDoctor, M3UPlaylistDoctor


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
        IPTVChannelDoctor.urlencode_logo(ch)
        self.assertTrue(ch.__eq__(expected), "the two channels are not equal")


class TestURLEncodeLogos(unittest.TestCase):
    def runTest(self):
        playlist = M3UPlaylist.loadf("tests/resources/m3u_plus_unencoded_logo.m3u")
        self.assertFalse(playlist.__eq__(tests.test_data.expected_urlencoded))
        M3UPlaylistDoctor.urlencode_logos(playlist)
        self.assertTrue(playlist.__eq__(tests.test_data.expected_urlencoded))


if __name__ == '__main__':
    unittest.main()
