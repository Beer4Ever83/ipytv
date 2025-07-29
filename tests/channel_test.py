import json
import unittest

from ipytv.channel import IPTVAttr, IPTVChannel
from ipytv.exceptions import MalformedExtinfException


class TestIPTVChannel(unittest.TestCase):

    def test_parse_m3u_plus_extinf_string(self):
        extinf_string = '''#EXTINF:-1 tvg-id="Rai1.it" tvg-name="Rai 1 SuperHD" tvg-logo="https://static.epg.best/it/RaiUno.it.png" group-title="SuperHD",Rai 1 SuperHD'''
        expected_attributes = {
            IPTVAttr.TVG_ID.value: "Rai1.it",
            IPTVAttr.TVG_NAME.value: "Rai 1 SuperHD",
            IPTVAttr.TVG_LOGO.value: "https://static.epg.best/it/RaiUno.it.png",
            IPTVAttr.GROUP_TITLE.value: "SuperHD"
        }
        expected = IPTVChannel(
            url="",
            name="Rai 1 SuperHD",
            duration="-1",
            attributes=expected_attributes
        )
        ch = IPTVChannel()
        ch.parse_extinf_string(extinf_string)
        self.assertEqual(expected, ch, "the two channels are not equal")

    def test_parse_m3u_plus_extinf_string_with_commas(self):
        extinf_string = '''#EXTINF:-1 tvg-id="" tvg-name="Io, Leonardo (2019)" tvg-logo="https://image.tmdb.org/t/p/w600_and_h900_bestv2/6DfpPu4iGrBswsyLdJlCwiLCudw.jpg" group-title="Recenti e Oggi al Cinema",Io, Leonardo (2019)'''
        expected_attributes = {
            IPTVAttr.TVG_ID.value: "",
            IPTVAttr.TVG_NAME.value: "Io, Leonardo (2019)",
            IPTVAttr.TVG_LOGO.value: "https://image.tmdb.org/t/p/w600_and_h900_bestv2/6DfpPu4iGrBswsyLdJlCwiLCudw.jpg",
            IPTVAttr.GROUP_TITLE.value: "Recenti e Oggi al Cinema"
        }
        expected = IPTVChannel(
            url="",
            name="Io, Leonardo (2019)",
            duration="-1",
            attributes=expected_attributes
        )
        ch = IPTVChannel()
        ch.parse_extinf_string(extinf_string)
        self.assertEqual(expected, ch, "the two channels are not equal")

    def test_parse_bad_m3u_plus_extinf_strings(self):
        extinf_strings = [
            ''' #EXTINF:-1 tvg-id="" tvg-name="" tvg-logo="" group-title="",Off The Map''',
            '''#EXTINF :-1 tvg-id="" tvg-name="" tvg-logo="" group-title="",Off The Map''',
            '''#EXTINF:-1 tvg-id="" tvg-name="" tvg-logo="" group-title="" Off The Map''',
            '''#EXTINF:-1 tvg/id="" tvg-name="" tvg-logo="" group-title="",Off The Map''',
            '''#EXTINF:-1 tvg-id="" tvg-name="" tvg-logo="" group-title="''',
            '''#EXTINF:-1tvg-id="" tvg-name="" tvg-logo="" group-title="",Off The Map'''
        ]
        for extinf_string in extinf_strings:
            ch = IPTVChannel()
            with self.assertRaises(MalformedExtinfException, msg=extinf_string):
                ch.parse_extinf_string(extinf_string)

    def test_parse_m3u_extinf_string(self):
        extinf_string = '''#EXTINF:-1,SANTUÁRIO DE FÁTIMA'''
        expected_attributes = {}
        expected = IPTVChannel(
            url="",
            name="SANTUÁRIO DE FÁTIMA",
            duration="-1",
            attributes=expected_attributes
        )
        ch = IPTVChannel()
        ch.parse_extinf_string(extinf_string)
        self.assertEqual(expected, ch, "the two channels are not equal")

    def test_copy(self):
        original_attributes = {
            IPTVAttr.TVG_ID.value: "Rai1.it",
            IPTVAttr.TVG_NAME.value: "Rai 1 SuperHD",
            IPTVAttr.TVG_LOGO.value: "https://static.epg.best/it/RaiUno.it.png",
            IPTVAttr.GROUP_TITLE.value: "SuperHD"
        }
        original = IPTVChannel(
            url="",
            name="Rai 1 SuperHD",
            duration="-1",
            attributes=original_attributes,
            extras=["#EXTVLCOPT:option1"]
        )
        clone = original.copy()
        self.assertEqual(original, clone)
        clone.name = "my " + clone.name
        self.assertNotEqual(original.name, clone.name)
        self.assertNotEqual(original, clone)

        clone = original.copy()
        self.assertEqual(original, clone)
        clone.attributes[IPTVAttr.TVG_NAME.value] = "Rai 2 SuperHD"
        self.assertNotEqual(original.attributes, clone.attributes)
        self.assertNotEqual(original, clone)

        clone = original.copy()
        self.assertEqual(original, clone)
        clone.extras.append("#EXTVLCOPT:option2")
        self.assertNotEqual(original.extras, clone.extras)
        self.assertNotEqual(original, clone)

    def test_to_string(self):
        original_attributes = {
            IPTVAttr.TVG_ID.value: "Rai1.it",
            IPTVAttr.TVG_NAME.value: "Rai 1 SuperHD",
            IPTVAttr.TVG_LOGO.value: "https://static.epg.best/it/RaiUno.it.png",
            IPTVAttr.GROUP_TITLE.value: "SuperHD"
        }
        original = IPTVChannel(
            url="",
            name="Rai 1 SuperHD",
            duration="-1",
            attributes=original_attributes
        )
        expected_output = '{name: "Rai 1 SuperHD", duration: "-1", url: "", attributes: {tvg-id: "Rai1.it", tvg-name: "Rai 1 SuperHD", tvg-logo: "https://static.epg.best/it/RaiUno.it.png", group-title: "SuperHD"}, extras: []}'
        real_output = str(original)
        self.assertEqual(expected_output, real_output)

    def test_to_dict(self):
        original_attributes = {
            IPTVAttr.TVG_ID.value: "Rai1.it",
            IPTVAttr.TVG_NAME.value: "Rai 1 SuperHD",
            IPTVAttr.TVG_LOGO.value: "https://static.epg.best/it/RaiUno.it.png",
            IPTVAttr.GROUP_TITLE.value: "SuperHD"
        }
        original_extras = [
            "#EXTVLCOPT:option1",
            "#EXTVLCOPT:option2"
        ]
        original = IPTVChannel(
            url="",
            name="Rai 1 SuperHD",
            duration="-1",
            attributes=original_attributes,
            extras=original_extras
        )
        expected_output = {
            "name": "Rai 1 SuperHD",
            "duration": "-1",
            "url": "",
            "attributes": {
                "tvg-id": "Rai1.it",
                "tvg-name": "Rai 1 SuperHD",
                "tvg-logo": "https://static.epg.best/it/RaiUno.it.png",
                "group-title": "SuperHD"
            },
            "extras": [
                "#EXTVLCOPT:option1",
                "#EXTVLCOPT:option2"
            ]
        }
        real_output = original.to_dict()
        self.assertEqual(expected_output, real_output)

    def test_to_json(self):
        original_attributes = {
            IPTVAttr.TVG_ID.value: "Rai1.it",
            IPTVAttr.TVG_NAME.value: "Rai 1 SuperHD",
            IPTVAttr.TVG_LOGO.value: "https://static.epg.best/it/RaiUno.it.png",
            IPTVAttr.GROUP_TITLE.value: "SuperHD"
        }
        original_extras = [
            "#EXTVLCOPT:option1",
            "#EXTVLCOPT:option2"
        ]
        original = IPTVChannel(
            url="",
            name="Rai 1 SuperHD",
            duration="-1",
            attributes=original_attributes,
            extras=original_extras
        )
        expected_output = json.dumps({
            "name": "Rai 1 SuperHD",
            "duration": "-1",
            "url": "",
            "attributes": {
                "tvg-id": "Rai1.it",
                "tvg-name": "Rai 1 SuperHD",
                "tvg-logo": "https://static.epg.best/it/RaiUno.it.png",
                "group-title": "SuperHD"
            },
            "extras": [
                "#EXTVLCOPT:option1",
                "#EXTVLCOPT:option2"
            ]
        })
        real_output = original.to_json()
        self.assertEqual(expected_output, real_output)


if __name__ == '__main__':
    unittest.main()
