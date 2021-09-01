import re
import shlex
from enum import Enum
from typing import Dict, List

from ipytv.exceptions import MalformedExtinfException


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
    __M3U_PLUS_EXTINF_PARSE_REGEX = r'^#EXTINF:(?P<duration_g>[-0-9\.]+)(?P<attributes_g>(\s+[\w-]+="[^"]*")*),(?P<name_g>.*)'

    def __init__(self, url: str = "", name: str = "", duration: str = "-1", attributes: Dict = None):
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
    def is_m3u_extinf_string(extinf_string: str) -> bool:
        return re.search(IPTVChannel.__M3U_EXTINF_REGEX, extinf_string) is not None

    @staticmethod
    def is_m3u_plus_extinf_string(extinf_string: str) -> bool:
        return re.search(IPTVChannel.__M3U_PLUS_EXTINF_REGEX, extinf_string) is not None

    def parse_extinf_string(self, extinf_string: str) -> None:
        m = re.match(IPTVChannel.__M3U_PLUS_EXTINF_PARSE_REGEX, extinf_string)
        if m is None:
            raise MalformedExtinfException("Malformed EXTINF string:\n{}".format(extinf_string))
        self.duration = m.group("duration_g")
        attributes = m.group("attributes_g")
        for entry in shlex.split(attributes):
            kv = entry.split("=")
            key = kv[0]
            value = kv[1]
            self.attributes[key] = value
        self.name = m.group("name_g")

    @staticmethod
    def from_playlist_entry(entry: List) -> 'IPTVChannel':
        channel = IPTVChannel()
        for row in entry:
            if str(row).startswith('#EXTINF:'):
                channel.parse_extinf_string(row)
            elif str(row).startswith('#'):
                # a comment or a non-supported tag
                pass
            else:
                channel.url = row
        return channel

    def __str__(self) -> str:
        attr_str = ''
        if len(self.attributes) > 0:
            for attr in self.attributes:
                attr_str += '{}: "{}", '.format(attr, self.attributes[attr])
        if attr_str.endswith(', '):
            attr_str = attr_str[:-2]
        out = '{{name: "{}", duration: "{}", url: "{}", attributes: {{{}}}}}'.format(
            self.name, self.duration, self.url, attr_str
        )
        return out
