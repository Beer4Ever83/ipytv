import logging
import shlex
from enum import Enum
from typing import Dict, List

from ipytv import m3u
from ipytv.exceptions import MalformedExtinfException

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class M3UEntry:
    def __init__(self, url: str, name: str = "", duration: str = "-1"):
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

    def __init__(self, url: str = "", name: str = "",
                 duration: str = "-1", attributes: Dict[str, str] = None,
                 extras: List[str] = None):
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
        return IPTVChannel(
            url=self.url,
            name=self.name,
            duration=self.duration,
            attributes=self.attributes.copy(),  # shallow copy is ok, as we're dealing with primitive types
            extras=self.extras.copy()           # shallow copy is ok, as we're dealing with primitive types
        )

    def parse_extinf_string(self, extinf_string: str) -> None:
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
        extinf_row = self._build_m3u_plus_extinf_entry()
        extras_rows = self._build_extras_entry()
        url_row = self._build_url_entry()
        return f'{extinf_row}{extras_rows}{url_row}'

    def to_m3u8_playlist_entry(self) -> str:
        extinf_row = self._build_m3u8_extinf_entry()
        url_row = self._build_url_entry()
        return f'{extinf_row}{url_row}'


def from_playlist_entry(entry: List[str]) -> 'IPTVChannel':
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
        else:
            channel.url = row
            log.info("URL row found")
    return channel
