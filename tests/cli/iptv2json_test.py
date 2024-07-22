import json
import unittest

from click.testing import CliRunner

from ipytv.cli.iptv2json import main as iptv2json_main


class TestIptv2Json(unittest.TestCase):
    def runTest(self):
        runner = CliRunner()
        input_playlist = "tests/resources/m3u_plus.m3u"
        result = runner.invoke(iptv2json_main, [input_playlist])
        self.assertEqual(0, result.exit_code)
        generated_json = json.loads(result.output)
        print(generated_json)
        with open("tests/resources/m3u_plus.json", "r") as f:
            expected_json = json.loads("\n".join(f.readlines()))
        self.assertEqual(expected_json, generated_json)


class TestIptv2JsonNoSanitize(unittest.TestCase):
    def runTest(self):
        runner = CliRunner()
        input_playlist = "tests/resources/m3u_plus.m3u"
        result = runner.invoke(iptv2json_main, [input_playlist, '--no-sanitize'])
        self.assertEqual(0, result.exit_code)
        generated_json = json.loads(result.output)
        with open("tests/resources/m3u_plus.json", "r", encoding='UTF-8') as f:
            expected_json = json.loads("\n".join(f.readlines()))
        self.assertEqual(expected_json, generated_json)


class TestIptv2JsonNoInputPlaylist(unittest.TestCase):
    def runTest(self):
        runner = CliRunner()
        result = runner.invoke(iptv2json_main, ['--no-sanitize'])
        self.assertNotEqual(0, result.exit_code)


class TestIptv2JsonMisspelledOption(unittest.TestCase):
    def runTest(self):
        runner = CliRunner()
        input_playlist = "tests/resources/m3u_plus.m3u"
        result = runner.invoke(iptv2json_main, [input_playlist, '--no-fanitize'])
        self.assertNotEqual(0, result.exit_code)


class TestIptv2JsonNoParms(unittest.TestCase):
    def runTest(self):
        runner = CliRunner()
        result = runner.invoke(iptv2json_main, [])
        self.assertNotEqual(0, result.exit_code)


if __name__ == '__main__':
    unittest.main()
