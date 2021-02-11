import re
import shlex
from enum import Enum

from ipytv.exceptions import MalformedExtinfException


class M3UEntry:
    def __init__(self, url, name="", duration=-1):
        self.url = url
        self.name = name
        self.duration = str(duration)

    def __eq__(self, other):
        return self.url == other.url and self.name == other.name and self.duration == other.duration


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
    M3U_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+,.*$'
    M3U_PLUS_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+(\s+[\w-]+="[^"]*")+,.*$'
    M3U_PLUS_EXTINF_PARSE_REGEX = r'^#EXTINF:(?P<duration_g>[-0-9\.]+)(?P<attributes_g>(\s+[\w-]+="[^"]*")*),(?P<name_g>.*)'

    def __init__(self, url="", name="", duration=-1, attributes=None):
        super().__init__(url, name, duration)
        self.attributes = attributes if attributes is not None else {}

    def __eq__(self, other):
        if isinstance(other, IPTVChannel) and \
                super().__eq__(other) and \
                self.attributes == other.attributes:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self):
        return IPTVChannel(
            url=self.url,
            name=self.name,
            duration=self.duration,
            attributes=self.attributes.copy()
        )

    @staticmethod
    def is_m3u_extinf_string(extinf_string):
        return re.search(IPTVChannel.M3U_EXTINF_REGEX, extinf_string)

    @staticmethod
    def is_m3u_plus_extinf_string(extinf_string):
        return re.search(IPTVChannel.M3U_PLUS_EXTINF_REGEX, extinf_string)

    def parse_extinf_string(self, extinf_string):
        m = re.match(IPTVChannel.M3U_PLUS_EXTINF_PARSE_REGEX, extinf_string)
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
    def from_playlist_entry(entry):
        channel = IPTVChannel()
        for row in entry:
            if str(row).startswith('#EXTINF:'):
                channel.parse_extinf_string(row)
            elif str(row).startswith('#'):
                # a comment or an unsupported tag
                pass
            else:
                channel.url = row
        return channel

    def __str__(self):
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
