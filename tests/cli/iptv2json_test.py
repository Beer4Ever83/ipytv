"""Tests for the iptv2json CLI command.

This module contains unit tests for the iptv2json command-line interface,
testing various scenarios including normal operation, options, and error cases.
"""
import json
import unittest

from click.testing import CliRunner

from ipytv.cli.iptv2json import iptv2json


class TestIptv2Json(unittest.TestCase):
    """Test cases for the iptv2json CLI command."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.runner = CliRunner()
        self.input_playlist = "tests/resources/m3u_plus.m3u"

    def test_basic_conversion(self) -> None:
        """Test basic M3U to JSON conversion functionality."""
        result = self.runner.invoke(iptv2json, [self.input_playlist])
        self.assertEqual(0, result.exit_code)
        generated_json = json.loads(result.output)
        with open("tests/resources/m3u_plus.json", "r", encoding='UTF-8') as f:
            expected_json = json.loads("\n".join(f.readlines()))
        self.assertEqual(expected_json, generated_json)

    def test_no_sanitize_option(self) -> None:
        """Test conversion with --no-sanitize option."""
        result = self.runner.invoke(iptv2json, [self.input_playlist, '--no-sanitize'])
        self.assertEqual(0, result.exit_code)
        generated_json = json.loads(result.output)
        with open("tests/resources/m3u_plus.json", "r", encoding='UTF-8') as f:
            expected_json = json.loads("\n".join(f.readlines()))
        self.assertEqual(expected_json, generated_json)

    def test_no_input_playlist(self) -> None:
        """Test behavior when no input playlist is provided."""
        result = self.runner.invoke(iptv2json, ['--no-sanitize'])
        self.assertNotEqual(0, result.exit_code)

    def test_misspelled_option(self) -> None:
        """Test behavior with misspelled command option."""
        result = self.runner.invoke(iptv2json, [self.input_playlist, '--no-fanitize'])
        self.assertNotEqual(0, result.exit_code)

    def test_no_parameters(self) -> None:
        """Test behavior when no parameters are provided."""
        result = self.runner.invoke(iptv2json, [])
        self.assertNotEqual(0, result.exit_code)


if __name__ == '__main__':
    unittest.main()