"""
Create and handle IPTV channels

Classes:
    M3UEntry
    IPTVAttr
    IPTVChannel

Functions:
    from_playlist_entry
"""
import logging
import shlex
from enum import Enum
from typing import Dict, List, Optional

from ipytv import m3u
from ipytv.exceptions import MalformedExtinfException

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class M3UEntry:
    """
    The base channel entity that models the standard #EXTINF and url rows in
    plain M3U playlists.

    Attributes
    ----------
    url: str
        The url where the medium can be found (can be a local file or a network
        resource)
    name: str
        The name of the channel or entry (the part after the last colon in an
        #EXTINF row)
    duration: str
        The duration of the channel or entry as a string formatted as a float or
        as an integer (with sign or not)
    """
    def __init__(self, url: str, name: str = "", duration: str = "-1"):
        """
        Parameters
        ----------
        url: str
            The url where the medium can be found (can be a local file or a network
            resource)
        name: str
            The name of the channel or entry (the part after the last colon in an
            #EXTINF row)
        duration: str
            The duration of the channel or entry as a string formatted as a float or
            as an integer (with sign or not)
        """
        self.url = url
        self.name = name
        self.duration = str(duration)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, M3UEntry) \
               and self.url == other.url \
               and self.name == other.name \
               and self.duration == other.duration

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)


class IPTVAttr(Enum):
    """
    An Enum class with a list of attributes commonly found in IPTV playlists
    (as part of the #EXTINF row)
    """
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


class IPTVChannel(M3UEntry):
    """
    A class that represents a channel in an IPTV playlist

    Attributes
    ----------
    url: str
        The url where the medium can be found (can be a local file or a network
        resource)
    name: str
        The name of the channel or entry (the part after the last colon in an
        #EXTINF row)
    duration: str
        The duration of the channel or entry as a string formatted as a float or
        as an integer (with sign or not)
    attributes: Dict[str, str]
        A dictionary with all the attributes as found in an #EXTINF string
    extras: List[str]
        A list of strings, containing all tags that are found between an #EXTINF
        row and its related url row (they are not parsed)

    Methods
    ----------
    copy() -> IPTVChannel
        Returns a copy of the object it's invoked on
    parse_extinf_string(extinf_string: str)
        Populates the channel with the information taken from the #EXTINF string
        passed as parameter. This method tries to parse well-formed strings as
        well as broken ones (i.e. #EXTINF rows with messed-up quotes)
    to_m3u_plus_playlist_entry() -> str
        Returns a string representation of this channel, as it was an entry of
        an IPTV playlist (in m3u_plus format)
    to_m3u8_playlist_entry() -> str
        Returns a string representation of this channel, as it was an entry of
        a standard m3u8 playlist
    """
    def __init__(self, url: str = "", name: str = "",
                 duration: str = "-1", attributes: Optional[Dict[str, str]] = None,
                 extras: Optional[List[str]] = None):
        super().__init__(url, name, duration)
        self.attributes: Dict[str, str] = attributes if attributes is not None else {}
        self.extras: List[str] = extras if extras is not None else []

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IPTVChannel) \
            and super().__eq__(other) \
            and self.attributes == other.attributes \
            and self.extras == other.extras

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def copy(self) -> 'IPTVChannel':
        """
        .. py:method:: Returns a copy of the object it's invoked on

        :return: a copy of this IPTVChannel object
        :rtype: IPTVChannel
        """
        return IPTVChannel(
            url=self.url,
            name=self.name,
            duration=self.duration,
            attributes=self.attributes.copy(),  # shallow copy is ok, as we're dealing with primitive types
            extras=self.extras.copy()           # shallow copy is ok, as we're dealing with primitive types
        )

    def parse_extinf_string(self, extinf_string: str) -> None:
        """
        .. py:method:: parse_extinf_string(extinf_string)

        Populates an IPTVChannel's fields with the attributes from an #EXTINF row

        :param str extinf_string:   The whole #EXTINF string as found in an IPTV
                                    playlist
        """
        match = m3u.match_m3u_plus_extinf_row(extinf_string)
        if match is not None:
            # Case of a well-formed EXTINF row
            log.info("parsing a well-formed EXTINF row:\n%s", extinf_string)
            self.duration = match.group("duration_g")
            log.info("duration: %s", self.duration)
            attributes = match.group("attributes_g")
            for entry in shlex.split(attributes):
                pair = entry.split("=", 1)
                key = pair[0]
                value = pair[1]
                self.attributes[key] = value
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
        attr_str = ''
        if len(self.attributes) > 0:
            for name, value in self.attributes.items():
                attr_str += f'{name}: "{value}", '
        if attr_str.endswith(', '):
            attr_str = attr_str[:-2]
        extras_str = ''
        if len(self.extras) > 0:
            for extra in self.extras:
                extras_str += f'{extra}, '
        if extras_str.endswith(', '):
            extras_str = extras_str[:-2]
        out = f'{{name: "{self.name}", duration: "{self.duration}", '\
              f'url: "{self.url}", attributes: {{{attr_str}}}, extras: [{extras_str}]}}'
        return out

    def _build_m3u_plus_extinf_entry(self) -> str:
        extinf_pattern = '#EXTINF:{}{},{}\n'
        attrs = ''
        for key, value in self.attributes.items():
            attrs += f' {key}="{value}"'
        return extinf_pattern.format(
            self.duration,
            attrs,
            self.name
        )

    def _build_m3u8_extinf_entry(self) -> str:
        extinf_pattern = '#EXTINF:{},{}\n'
        return extinf_pattern.format(
            self.duration,
            self.name
        )

    def _build_extras_entry(self) -> str:
        out = ''
        for extra in self.extras:
            out += f'{extra}\n'
        return out

    def _build_url_entry(self) -> str:
        return f"{self.url}\n"

    def to_m3u_plus_playlist_entry(self) -> str:
        """
        .. py:method:: to_m3u_plus_playlist_entry

        Converts the current object into a string suitable for an IPTV playlist
        in the m3u_plus format. Please note that the string may contain multiple
        newline-separated rows.

        :return:    a string with one or more rows describing this channel in
                    m3u_plus format.
        :rtype:     str
        """
        extinf_row = self._build_m3u_plus_extinf_entry()
        extras_rows = self._build_extras_entry()
        url_row = self._build_url_entry()
        return f'{extinf_row}{extras_rows}{url_row}'

    def to_m3u8_playlist_entry(self) -> str:
        """
        .. py:method:: to_m3u8_playlist_entry

        Converts the current object into a string suitable for a regular M3U
        playlist in the m3u8 format. Please note that the string may contain
        up to 2 newline-separated rows.

        :return:    a string with one or more rows describing this channel in
                    m3u8 format.
        :rtype:     str
        """
        extinf_row = self._build_m3u8_extinf_entry()
        url_row = self._build_url_entry()
        return f'{extinf_row}{url_row}'


def from_playlist_entry(entry: List[str]) -> 'IPTVChannel':
    """
    .. py:function:: from_playlist_entry(entry)

    Builds an IPTVChannel object from one or more rows from a playlist.
    A playlist entry can be composed of one or more rows. In its simplest form,
    only the url row is present, but the most common case has two rows: the
    #EXTINF and the url row. In all other cases, all the tags included between
    an #EXTINF row and the related url row are considered as part of a channel.

    :param:     entry
    :type:      List[str]

    :return:    An IPTVChannel object whose fields are populated with info from
                the playlist rows.
    :rtype:     IPTVChannel
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
