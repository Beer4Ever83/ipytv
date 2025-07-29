"""Tests for the json2iptv CLI command.

This module contains unit tests for the json2iptv command-line interface,
testing various scenarios including normal operation and error cases.
"""
import unittest

from click.testing import CliRunner

from ipytv import playlist
from ipytv.cli.json2iptv import json2iptv


class TestJson2Iptv(unittest.TestCase):
    """Test cases for the json2iptv CLI command."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.runner = CliRunner()

    def test_basic_conversion(self) -> None:
        """Test basic JSON to M3U conversion functionality."""
        input_json = "tests/resources/m3u_plus.json"
        result = self.runner.invoke(json2iptv, [input_json])
        self.assertEqual(0, result.exit_code, result.output)
        generated_pl = playlist.loads(result.output)
        expected_pl = playlist.loadf("tests/resources/m3u_plus.m3u")
        self.assertEqual(expected_pl, generated_pl)

    def test_no_parameters(self) -> None:
        """Test behavior when no parameters are provided."""
        result = self.runner.invoke(json2iptv, [])
        self.assertNotEqual(0, result.exit_code, result.output)

    def test_bad_json_file(self) -> None:
        """Test behavior with unsupported JSON file."""
        input_json = "tests/resources/unsupported.json"
        result = self.runner.invoke(json2iptv, [input_json])
        self.assertNotEqual(0, result.exit_code, result.output)


if __name__ == '__main__':
    unittest.main()
