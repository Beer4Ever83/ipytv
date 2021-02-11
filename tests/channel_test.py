import unittest

from ipytv import IPTVAttr, IPTVChannel, MalformedExtinfException


class TestIsM3UPlusExtinfString(unittest.TestCase):
    def runTest(self):
        extinf_string = '''#EXTINF:-1 tvg-id="" tvg-name="Io, Leonardo (2019)" tvg-logo="https://image.tmdb.org/t/p/w600_and_h900_bestv2/6DfpPu4iGrBswsyLdJlCwiLCudw.jpg" group-title="Recenti e Oggi al Cinema",Io, Leonardo (2019)'''
        self.assertTrue(IPTVChannel.is_m3u_plus_extinf_string(extinf_string))


class TestIsNotM3UPlusExtinfString(unittest.TestCase):
    def runTest(self):
        extinf_string = '''#EXTINF:-1,SANTUÁRIO DE FÁTIMA'''
        self.assertFalse(IPTVChannel.is_m3u_plus_extinf_string(extinf_string))


class TestIsM3UExtinfString(unittest.TestCase):
    def runTest(self):
        extinf_string = '''#EXTINF:-1,SANTUÁRIO DE FÁTIMA'''
        self.assertTrue(IPTVChannel.is_m3u_extinf_string(extinf_string))


class TestIsNotM3UExtinfString(unittest.TestCase):
    def runTest(self):
        extinf_string = '''#EXTINF:-1 tvg-id="" tvg-name="Io, Leonardo (2019)" tvg-logo="https://image.tmdb.org/t/p/w600_and_h900_bestv2/6DfpPu4iGrBswsyLdJlCwiLCudw.jpg" group-title="Recenti e Oggi al Cinema",Io, Leonardo (2019)'''
        self.assertFalse(IPTVChannel.is_m3u_extinf_string(extinf_string))


class TestParseM3UPlusExtinfString(unittest.TestCase):
    def runTest(self):
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
            duration=-1,
            attributes=expected_attributes
        )
        ch = IPTVChannel()
        ch.parse_extinf_string(extinf_string)
        self.assertTrue(ch.__eq__(expected), "the two channels are not equal")


class TestParseM3UPlusExtinfStringWithCommas(unittest.TestCase):
    def runTest(self):
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
            duration=-1,
            attributes=expected_attributes
        )
        ch = IPTVChannel()
        ch.parse_extinf_string(extinf_string)
        self.assertTrue(ch.__eq__(expected), "the two channels are not equal")


class TestParseBadM3UPlusExtinfStrings(unittest.TestCase):
    def runTest(self):
        extinf_strings = [
            ''' #EXTINF:-1 tvg-id="" tvg-name="" tvg-logo="" group-title="",Off The Map''',
            '''#EXTINF :-1 tvg-id="" tvg-name="" tvg-logo="" group-title="",Off The Map''',
            '''#EXTINF:-1 tvg-id=" tvg-name="" tvg-logo="" group-title="",Off The Map''',
            '''#EXTINF:-1 tvg-id="" tvg-name="" tvg-logo="" group-title="" Off The Map''',
            '''#EXTINF:-1 tvg/id="" tvg-name="" tvg-logo="" group-title="",Off The Map''',
            '''#EXTINF:-1 tvg-id="" tvg-name="" tvg-logo="" group-title="''',
            '''#EXTINF:-1tvg-id="" tvg-name="" tvg-logo="" group-title="",Off The Map''',
            '''#EXTINF:-1 tvg-id=""tvg-name="" tvg-logo="" group-title="",Off The Map'''
        ]
        for extinf_string in extinf_strings:
            ch = IPTVChannel()
            self.assertRaises(MalformedExtinfException, ch.parse_extinf_string, extinf_string)


class TestParseM3UExtinfString(unittest.TestCase):
    def runTest(self):
        extinf_string = '''#EXTINF:-1,SANTUÁRIO DE FÁTIMA'''
        expected_attributes = {}
        expected = IPTVChannel(
            url="",
            name="SANTUÁRIO DE FÁTIMA",
            duration=-1,
            attributes=expected_attributes
        )
        ch = IPTVChannel()
        ch.parse_extinf_string(extinf_string)
        self.assertTrue(ch.__eq__(expected), "the two channels are not equal")


class TestCopy(unittest.TestCase):
    def runTest(self):
        original_attributes = {
            IPTVAttr.TVG_ID.value: "Rai1.it",
            IPTVAttr.TVG_NAME.value: "Rai 1 SuperHD",
            IPTVAttr.TVG_LOGO.value: "https://static.epg.best/it/RaiUno.it.png",
            IPTVAttr.GROUP_TITLE.value: "SuperHD"
        }
        original = IPTVChannel(
            url="",
            name="Rai 1 SuperHD",
            duration=-1,
            attributes=original_attributes
        )
        clone = original.copy()
        self.assertTrue(original == clone)
        clone.name = "my " + clone.name
        self.assertTrue(original != clone)
        self.assertTrue("my " + original.name == clone.name)


class TestToString(unittest.TestCase):
    def runTest(self):
        original_attributes = {
            IPTVAttr.TVG_ID.value: "Rai1.it",
            IPTVAttr.TVG_NAME.value: "Rai 1 SuperHD",
            IPTVAttr.TVG_LOGO.value: "https://static.epg.best/it/RaiUno.it.png",
            IPTVAttr.GROUP_TITLE.value: "SuperHD"
        }
        original = IPTVChannel(
            url="",
            name="Rai 1 SuperHD",
            duration=-1,
            attributes=original_attributes
        )
        expected_output = '{name: "Rai 1 SuperHD", duration: "-1", url: "", attributes: {tvg-id: "Rai1.it", tvg-name: "Rai 1 SuperHD", tvg-logo: "https://static.epg.best/it/RaiUno.it.png", group-title: "SuperHD"}}'
        real_output = str(original)
        self.assertEqual(expected_output, real_output)


if __name__ == '__main__':
    unittest.main()
