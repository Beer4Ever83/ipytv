"""Fix common errors in M3U files and IPTV channels.

This module provides classes to sanitize and repair common formatting issues
found in M3U and IPTV playlist files, including malformed quotes, unquoted
numeric attributes, and incorrect attribute names.

Classes:
    M3UDoctor: Fixes structural issues in M3U file rows
    IPTVChannelDoctor: Sanitizes individual IPTV channel attributes
    M3UPlaylistDoctor: Applies fixes to entire M3U playlists
"""
import logging
import re
import urllib.parse
from typing import List

from ipytv import m3u
from ipytv.channel import IPTVChannel, IPTVAttr
from ipytv.playlist import M3UPlaylist

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# Pre-compiled regular expressions for better performance
_SPLIT_QUOTED_STRING_PATTERN = re.compile(r"^\s*\"")
_UNQUOTED_NUMBERS_PATTERN = re.compile(r"(?P<attribute_g>\s+(?P<name_g>[\w-]+)=\s*(?P<value_g>-?\d+(?:\.\d+)?))")
_SPACES_BEFORE_COMMA_PATTERN = re.compile(r"^#EXTINF:(?P<duration_g>[-0-9\.]+)(?P<spaces_g>\s)+,(?P<name_g>.*)")


class M3UDoctor:
    """Fixes structural issues in M3U file rows.

    Provides static methods to repair common formatting problems in M3U files
    such as split quoted strings, unquoted numeric attributes, and spacing issues.
    """

    @staticmethod
    def _fix_split_quoted_string(m3u_rows: List) -> List:
        """Fix rows with quoted strings split across multiple lines.

        Handles cases where quoted attribute values are broken across lines,
        typically due to line breaks within quoted strings.

        Args:
            m3u_rows: List of M3U file rows that may contain split quoted strings.

        Returns:
            List of M3U rows with split quoted strings merged back together.

        Example:
            Input rows:
                ['#EXTINF:-1 tvg-id="Cinema1', '" tvg-name="Cinema1",...']
            Output:
                ['#EXTINF:-1 tvg-id="Cinema1" tvg-name="Cinema1",...']
        """
        fixed_m3u_rows: List = []
        for current_row in m3u_rows:
            new_row = current_row
            if _SPLIT_QUOTED_STRING_PATTERN.match(current_row) and \
                    len(fixed_m3u_rows) > 0 and \
                    m3u.is_extinf_row(fixed_m3u_rows[-1]):
                previous_row = fixed_m3u_rows.pop()
                new_row = previous_row.rstrip() + current_row.lstrip()
            fixed_m3u_rows.append(new_row)
        return fixed_m3u_rows

    @staticmethod
    def _fix_unquoted_numeric_attributes(m3u_rows: List[str]) -> List:
        """Fix unquoted numeric attribute values in EXTM3U and EXTINF rows.

        Adds proper double quotes around numeric attribute values that should
        be quoted according to M3U Plus specification.

        Args:
            m3u_rows: List of M3U file rows that may contain unquoted numeric attributes.

        Returns:
            List of M3U rows with numeric attributes properly quoted.

        Example:
            Input:
                '#EXTINF:-1 tvg-shift=-10.5 tvg-id=22,Channel'
            Output:
                '#EXTINF:-1 tvg-shift="-10.5" tvg-id="22",Channel'
        """
        fixed_m3u_rows: List = []
        for current_row in m3u_rows:
            new_row = current_row
            if m3u.is_m3u_header_row(current_row) or m3u.is_extinf_row(current_row):
                for match in _UNQUOTED_NUMBERS_PATTERN.finditer(current_row):
                    attribute = match.group("attribute_g")
                    name = match.group("name_g")
                    value = match.group("value_g")
                    new_row = new_row.replace(attribute, f" {name}=\"{value}\"")
            fixed_m3u_rows.append(new_row)
        return fixed_m3u_rows

    @staticmethod
    def _fix_space_before_comma(m3u_rows: List[str]) -> List:
        """Fix EXTINF rows with spaces between duration and comma.

        Removes extraneous spaces in EXTINF rows that have no attributes
        but contain spaces before the comma separator.

        Args:
            m3u_rows: List of M3U file rows that may have spacing issues.

        Returns:
            List of M3U rows with proper spacing around commas.

        Example:
            Input:
                '#EXTINF:-1 ,Channel 22'
            Output:
                '#EXTINF:-1,Channel 22'
        """
        fixed_m3u_rows: List = []
        for current_row in m3u_rows:
            new_row = current_row
            if m3u.is_extinf_row(current_row):
                match = _SPACES_BEFORE_COMMA_PATTERN.match(current_row)
                if match:
                    new_row = f"#EXTINF:{match.group('duration_g')},{match.group('name_g')}"
            fixed_m3u_rows.append(new_row)
        return fixed_m3u_rows

    @staticmethod
    def sanitize(m3u_rows: List) -> List:
        """Apply all M3U file fixes to a list of rows.

        Sequentially applies all available fixes to repair common M3U file
        formatting issues.

        Args:
            m3u_rows: List of raw M3U file rows that may contain various formatting issues.

        Returns:
            List of M3U rows with formatting issues corrected.

        Example:
            >>> rows = ['#EXTINF:-1 tvg-id=123 ,Channel']
            >>> fixed = M3UDoctor.sanitize(rows)
            >>> fixed[0]
            '#EXTINF:-1 tvg-id="123",Channel'
        """
        fixed = M3UDoctor._fix_split_quoted_string(m3u_rows)
        fixed = M3UDoctor._fix_unquoted_numeric_attributes(fixed)
        fixed = M3UDoctor._fix_space_before_comma(fixed)
        return fixed


class IPTVChannelDoctor:
    """Sanitizes individual IPTV channel attributes and values.

    Provides methods to fix common issues with IPTV channel attributes
    such as URL encoding, attribute name normalization, and comma handling.
    """

    @staticmethod
    def _urlencode_value(chan: IPTVChannel, attribute_name: str) -> None:
        """URL-encode an attribute value if the attribute exists.

        Applies proper URL encoding to attribute values, particularly useful
        for tvg-logo URLs that may contain special characters.

        Args:
            chan: The IPTVChannel to modify in-place.
            attribute_name: Name of the attribute to URL-encode.

        Example:
            For tvg-logo="https://site.com/image,file.jpg":
            Result: tvg-logo="https://site.com/image%2Cfile.jpg"
        """
        if attribute_name in chan.attributes:
            value = chan.attributes[attribute_name]
            chan.attributes[attribute_name] = urllib.parse.quote(value, safe=':/%?&=')

    @staticmethod
    def _normalize_attributes_name(chan: IPTVChannel, attribute_name: str) -> None:
        """Normalize attribute names to standard IPTV conventions.

        Corrects common misspellings and case issues in well-known IPTV
        attribute names by converting them to lowercase standard forms.

        Args:
            chan: The IPTVChannel to modify in-place.
            attribute_name: Name of the attribute to normalize.

        Example:
            Changes "tvg-ID" to "tvg-id", "GROUP-TITLE" to "group-title"
        """
        try:
            IPTVAttr(attribute_name)
        except ValueError:
            try:
                key = IPTVAttr(attribute_name.lower()).value
                value = chan.attributes[attribute_name]
                del chan.attributes[attribute_name]
                chan.attributes[key] = value
            except ValueError:
                # It seems not a well-known attribute, so we leave it untouched.
                pass

    @staticmethod
    def _convert_commas(chan: IPTVChannel, attribute_name: str) -> None:
        """Replace commas in attribute values with underscores.

        Converts commas to underscores in attribute values to prevent parsing
        issues with libraries that don't handle commas properly. Skips tvg-logo
        attributes as they may legitimately contain commas in URLs.

        Args:
            chan: The IPTVChannel to modify in-place.
            attribute_name: Name of the attribute to process.

        Example:
            Changes group-title="News, Sports" to group-title="News_ Sports"
        """
        if attribute_name == IPTVAttr.TVG_LOGO.value:
            return
        value: str = chan.attributes[attribute_name]
        if "," in value:
            value = value.replace(",", "_")
            chan.attributes[attribute_name] = value

    @staticmethod
    def sanitize(chan: IPTVChannel) -> IPTVChannel:
        """Apply all channel-level fixes to an IPTV channel.

        Creates a copy of the channel and applies all available sanitization
        fixes including URL encoding, comma conversion, and attribute normalization.

        Args:
            chan: The original IPTVChannel to sanitize.

        Returns:
            A new IPTVChannel instance with all fixes applied.

        Example:
            >>> channel = IPTVChannel(attributes={"tvg-ID": "123", "title": "News,Sports"})
            >>> clean = IPTVChannelDoctor.sanitize(channel)
            >>> clean.attributes["tvg-id"]  # normalized
            '123'
            >>> clean.attributes["title"]   # comma replaced
            'News_Sports'
        """
        attr: str
        new_chan = chan.copy()
        IPTVChannelDoctor._urlencode_value(new_chan, IPTVAttr.TVG_LOGO.value)
        for attr in chan.attributes.keys():
            IPTVChannelDoctor._convert_commas(new_chan, attr)
            IPTVChannelDoctor._normalize_attributes_name(new_chan, attr)
        return new_chan


class M3UPlaylistDoctor:
    """Applies sanitization fixes to entire M3U playlists.

    Provides methods to clean up complete IPTV playlists by applying
    channel-level fixes to all channels while preserving playlist attributes.
    """

    @staticmethod
    def sanitize(playlist: M3UPlaylist) -> M3UPlaylist:
        """Apply sanitization fixes to all channels in a playlist.

        Creates a new playlist with all channels sanitized using IPTVChannelDoctor.
        Preserves all playlist-level attributes from the original.

        Args:
            playlist: The original M3UPlaylist to sanitize.

        Returns:
            A new M3UPlaylist with all channels sanitized and attributes preserved.

        Example:
            >>> original = M3UPlaylist()
            >>> # ... add channels with issues ...
            >>> clean_playlist = M3UPlaylistDoctor.sanitize(original)
            >>> # All channels now have normalized attributes
        """
        new_playlist: M3UPlaylist = M3UPlaylist()
        new_playlist.add_attributes(playlist.get_attributes())
        chan: IPTVChannel
        for chan in playlist:
            new_playlist.append_channel(IPTVChannelDoctor.sanitize(chan))
        return new_playlist


if __name__ == "__main__":
    pass
