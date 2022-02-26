import logging
import re
import shlex
from enum import Enum
from typing import Dict, List

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


class IPTVChannel(M3UEntry):
    __M3U_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+,.*$'
    __M3U_PLUS_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+(\s+[\w-]+="[^"]*")+,.*$'
    __M3U_PLUS_EXTINF_PARSE_REGEX = r'^#EXTINF:(?P<duration_g>[-0-9\.]+)'\
                                    r'(?P<attributes_g>(\s+[\w-]+="[^"]*")*),'\
                                    r'(?P<name_g>.*)'

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

    @staticmethod
    def is_m3u_header(row: str) -> bool:
        return row == "#EXTM3U"

    @staticmethod
    def is_m3u_extinf_string(extinf_string: str) -> bool:
        return re.search(IPTVChannel.__M3U_EXTINF_REGEX, extinf_string) is not None

    @staticmethod
    def is_m3u_plus_extinf_string(extinf_string: str) -> bool:
        return re.search(IPTVChannel.__M3U_PLUS_EXTINF_REGEX, extinf_string) is not None

    @staticmethod
    def is_extinf_string(extinf_string: str) -> bool:
        return extinf_string.startswith("#EXTINF")

    @staticmethod
    def is_comment_or_tag(string: str) -> bool:
        string.startswith('#')

    def parse_extinf_string(self, extinf_string: str) -> None:
        match = re.match(IPTVChannel.__M3U_PLUS_EXTINF_PARSE_REGEX, extinf_string)
        if match is None:
            log.error(f"malformed #EXTINF row: {extinf_string}")
            raise MalformedExtinfException(f"Malformed EXTINF string:\n{extinf_string}")
        self.duration = match.group("duration_g")
        log.info(f"duration: {self.duration}")
        attributes = match.group("attributes_g")
        for entry in shlex.split(attributes):
            pair = entry.split("=")
            key = pair[0]
            value = pair[1]
            self.attributes[key] = value
        log.info(f"attributes: {self.attributes}")
        self.name = match.group("name_g")
        log.info(f"name: {self.name}")

    @staticmethod
    def from_playlist_entry(entry: List[str]) -> 'IPTVChannel':
        channel = IPTVChannel()
        for row in entry:
            if IPTVChannel.is_extinf_string(row):
                channel.parse_extinf_string(row)
                log.info("#EXTINFO row found")
            elif IPTVChannel.is_comment_or_tag(row):
                # a comment or a non-supported tag
                log.warning(f"commented row or unsupported tag found: {row}")
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
