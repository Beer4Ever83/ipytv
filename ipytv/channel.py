import logging
import shlex
from enum import Enum
from typing import Dict, List

from ipytv import m3u_tools
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


class IPTVChannel(M3UEntry):

    def __init__(self, url: str = "", name: str = "",
                 duration: str = "-1", attributes: Dict = None):
        super().__init__(url, name, duration)
        self.attributes = attributes if attributes is not None else {}

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IPTVChannel) \
               and super().__eq__(other) \
               and self.attributes == other.attributes

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def copy(self) -> 'IPTVChannel':
        return IPTVChannel(
            url=self.url,
            name=self.name,
            duration=self.duration,
            attributes=self.attributes.copy()
        )

    def parse_extinf_string(self, extinf_string: str) -> None:
        match = m3u_tools.match_m3u_plus_extinf_row(extinf_string)
        if match is None:
            log.error("malformed #EXTINF row: %s", extinf_string)
            raise MalformedExtinfException(f"Malformed EXTINF string:\n{extinf_string}")
        self.duration = match.group("duration_g")
        log.info("duration: %s", self.duration)
        attributes = match.group("attributes_g")
        for entry in shlex.split(attributes):
            pair = entry.split("=")
            key = pair[0]
            value = pair[1]
            self.attributes[key] = value
        log.info("attributes: %s", self.attributes)
        self.name = match.group("name_g")
        log.info("name: %s", self.name)

    @staticmethod
    def from_playlist_entry(entry: List[str]) -> 'IPTVChannel':
        channel = IPTVChannel()
        for row in entry:
            if m3u_tools.is_extinf_row(row):
                channel.parse_extinf_string(row)
                log.info("#EXTINFO row found")
            elif m3u_tools.is_comment_or_tag_row(row):
                # a comment or a non-supported tag
                log.warning("commented row or unsupported tag found in \"%s\"", row)
            else:
                channel.url = row
                log.info("URL row found")
        return channel

    def __str__(self) -> str:
        attr_str = ''
        if len(self.attributes) > 0:
            for attr in self.attributes:
                attr_str += f'{attr}: "{self.attributes[attr]}", '
        if attr_str.endswith(', '):
            attr_str = attr_str[:-2]
        out = f'{{name: "{self.name}", duration: "{self.duration}", '\
              f'url: "{self.url}", attributes: {{{attr_str}}}}}'
        return out
