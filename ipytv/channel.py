"""Create and handle IPTV channels.

This module provides classes for representing IPTV channels and playlist entries,
along with utilities for parsing EXTINF rows and converting between formats.

Classes:
    IPTVAttr: Enum of common IPTV attributes
    IPTVChannel: Extended M3U entry with IPTV-specific features

Functions:
    from_playlist_entry: Create an IPTVChannel from playlist rows
"""

import json
import logging
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any, Self

from ipytv import m3u
from ipytv.exceptions import MalformedExtinfException

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class IPTVAttr(StrEnum):
    """Enum of attributes commonly found in IPTV playlists as part of #EXTINF rows."""

    TVG_ID = "tvg-id"
    TVG_NAME = "tvg-name"
    TVG_LANGUAGE = "tvg-language"
    TVG_LOGO = "tvg-logo"
    TVG_LOGO_SMALL = "tvg-logo-small"
    TVG_COUNTRY = "tvg-country"
    GROUP_TITLE = "group-title"
    PARENT_CODE = "parent-code"
    AUDIO_TRACK = "audio-track"
    TVG_SHIFT = "tvg-shift"
    TVG_REC = "tvg-rec"
    ASPECT_RATIO = "aspect-ratio"
    TVG_CHNO = "tvg-chno"
    RADIO = "radio"
    TVG_URL = "tvg-url"


@dataclass(slots=True)
class IPTVChannel:
    """A channel in an IPTV playlist with attributes and metadata.

    Attributes:
        url: The URL where the medium can be found.
        name: The name of the channel.
        duration: The duration as a string.
        attributes: Dictionary of all attributes found in the #EXTINF string.
        extras: List of tags found between #EXTINF row and its related URL row.
    """

    url: str = ""
    name: str = ""
    duration: str = "-1"
    attributes: dict[str, str] = field(default_factory=dict)
    extras: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Backwards compatibility: accept non-string durations and explicit None collections.
        self.duration = str(self.duration)
        if self.attributes is None:
            self.attributes = {}
        if self.extras is None:
            self.extras = []

    def copy(self) -> Self:
        """Create a copy of this IPTVChannel object.

        Returns:
            A new IPTVChannel instance with copied values.
        """
        # Shallow copies are enough, as the collections only hold strings.
        return replace(self, attributes=self.attributes.copy(), extras=self.extras.copy())

    def parse_extinf_string(self, extinf_string: str) -> None:
        """Parse an #EXTINF string and populate the channel's fields.

        Handles both well-formed and malformed #EXTINF rows with quoting issues.

        Args:
            extinf_string: The complete #EXTINF string from an IPTV playlist.

        Raises:
            MalformedExtinfException: If the EXTINF string cannot be parsed.

        Example:
            >>> channel = IPTVChannel()
            >>> channel.parse_extinf_string('#EXTINF:-1 tvg-id="1",Channel Name')
            >>> channel.name
            'Channel Name'
        """
        match = m3u.match_m3u_plus_extinf_row(extinf_string)
        if match is not None:
            # Case of a well-formed EXTINF row
            log.info("parsing a well-formed EXTINF row:\n%s", extinf_string)
            self.duration = match.group("duration_g")
            log.info("duration: %s", self.duration)
            attributes = match.group("attributes_g")
            self.attributes = m3u.parse_attributes(attributes)
            log.info("attributes: %s", self.attributes)
            self.name = match.group("name_g")
            log.info("name: %s", self.name)
            return

        match = m3u.match_m3u_plus_broken_extinf_row(extinf_string)
        if match is not None:
            # Case of a broken #EXTINF row (with quoting issues)
            log.warning("parsing an EXTINF row with quoting issues:\n%s", extinf_string)
            self.duration = match.group("duration_g")
            log.info("duration: %s", self.duration)
            self.attributes = m3u.get_m3u_plus_broken_attributes(extinf_string)
            log.info("attributes: %s", self.attributes)
            self.name = match.group("name_g")
            log.info("name: %s", self.name)
            return

        # This EXTINF row can't be parsed
        log.error("malformed #EXTINF row: %s", extinf_string)
        raise MalformedExtinfException(f"Malformed #EXTINF string:\n{extinf_string}")

    def __str__(self) -> str:
        attr_str = ", ".join(f'{name}: "{value}"' for name, value in self.attributes.items())
        extras_str = ", ".join(self.extras)
        return (
            f'{{name: "{self.name}", duration: "{self.duration}", '
            f'url: "{self.url}", attributes: {{{attr_str}}}, extras: [{extras_str}]}}'
        )

    def _build_m3u_plus_extinf_entry(self) -> str:
        extinf_pattern = "#EXTINF:{}{},{}\n"
        attrs = ""
        for key, value in self.attributes.items():
            attrs += f' {key}="{value}"'
        return extinf_pattern.format(self.duration, attrs, self.name)

    def _build_m3u8_extinf_entry(self) -> str:
        extinf_pattern = "#EXTINF:{},{}\n"
        return extinf_pattern.format(self.duration, self.name)

    def _build_extras_entry(self) -> str:
        if not self.extras:
            return ""
        return "\n".join(self.extras) + "\n"

    def _build_url_entry(self) -> str:
        return f"{self.url}\n"

    def to_m3u_plus_playlist_entry(self) -> str:
        """Convert the channel to M3U Plus playlist format.

        Returns:
            A string with one or more newline-separated rows describing this
            channel in M3U Plus format.

        Example:
            >>> channel = IPTVChannel(url="http://example.com", name="Test")
            >>> entry = channel.to_m3u_plus_playlist_entry()
            >>> "#EXTINF:" in entry
            True
        """
        extinf_row = self._build_m3u_plus_extinf_entry()
        extras_rows = self._build_extras_entry()
        url_row = self._build_url_entry()
        return f"{extinf_row}{extras_rows}{url_row}"

    def to_m3u8_playlist_entry(self) -> str:
        """Convert the channel to standard M3U8 playlist format.

        Returns:
            A string with one or more newline-separated rows describing this
            channel in M3U8 format (without extended attributes).

        Example:
            >>> channel = IPTVChannel(url="http://example.com", name="Test")
            >>> entry = channel.to_m3u8_playlist_entry()
            >>> "tvg-" not in entry
            True
        """
        extinf_row = self._build_m3u8_extinf_entry()
        url_row = self._build_url_entry()
        return f"{extinf_row}{url_row}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize the channel to a dictionary.

        Returns:
            A dictionary containing all channel fields.

        Example:
            >>> channel = IPTVChannel(name="Test", url="http://example.com")
            >>> data = channel.to_dict()
            >>> data['name']
            'Test'
        """
        return {
            "name": self.name,
            "duration": self.duration,
            "url": self.url,
            "attributes": self.attributes,
            "extras": self.extras,
        }

    def to_json(self) -> str:
        """Serialize the channel to JSON format.

        Returns:
            A JSON string representation of the channel's fields.

        Example:
            >>> channel = IPTVChannel(name="Test")
            >>> json_str = channel.to_json()
            >>> '"name": "Test"' in json_str
            True
        """
        return json.dumps(self.to_dict())


def from_playlist_entry(entry: list[str]) -> IPTVChannel:
    """Build an IPTVChannel object from playlist rows.

    A playlist entry can contain multiple rows: #EXTINF row, additional tags,
    and the URL row. All tags between #EXTINF and URL are stored as extras.

    Args:
        entry: One or more rows belonging to the same channel from an IPTV playlist.

    Returns:
        An IPTVChannel object with fields populated from the playlist rows.

    Example:
        >>> rows = ['#EXTINF:-1,Test Channel', 'http://example.com/stream']
        >>> channel = from_playlist_entry(rows)
        >>> channel.name
        'Test Channel'
    """
    channel = IPTVChannel()
    for row in entry:
        if m3u.is_extinf_row(row):
            try:
                channel.parse_extinf_string(row)
            except MalformedExtinfException:
                log.warning("Skipping the following entry as it contains a malformed #EXTINF row:\n%s", entry)
            log.info("#EXTINF row found")
        elif m3u.is_comment_or_tag_row(row):
            # a comment or a non-supported tag, we add it to extras
            channel.extras.append(row)
            log.warning("commented row or unsupported tag found:\n%s", row)
        elif m3u.is_url_row(row):
            channel.url = row
            log.info("URL row found")
    return channel


if __name__ == "__main__":
    pass
