import json
import unittest

from click.testing import CliRunner
from ipytv import playlist
from ipytv.cli.json2iptv import main as json2iptv_main


class TestJson2Iptv(unittest.TestCase):
    def runTest(self):
        runner = CliRunner()
        input_json = "tests/resources/m3u_plus.json"
        result = runner.invoke(json2iptv_main, [input_json])
        self.assertEqual(0, result.exit_code)
        generated_pl = playlist.loads(result.output)
        expected_pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        self.assertEqual(expected_pl, generated_pl)


class TestJson2IptvNoParms(unittest.TestCase):
    def runTest(self):
        runner = CliRunner()
        result = runner.invoke(json2iptv_main, [])
        self.assertNotEqual(0, result.exit_code)


class TestJson2IptvBadJson(unittest.TestCase):
    def runTest(self):
        runner = CliRunner()
        input_json = "tests/resources/unsupported.json"
        result = runner.invoke(json2iptv_main, [input_json])
        self.assertNotEqual(0, result.exit_code)


if __name__ == '__main__':
    unittest.main()
