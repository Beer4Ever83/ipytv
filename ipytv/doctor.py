"""Fix common errors in M3U files and IPTV channels

Classes:
    M3UDoctor
    IPTVChannelDoctor
    M3UPlaylistDoctor
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


class M3UDoctor:
    @staticmethod
    def _fix_split_quoted_string(m3u_rows: List) -> List:
        """
        This covers the case of rows beginning with double quotes that belong to the previous row.
        Example:
            #EXTINF:-1 tvg-id="Cinema1
            " tvg-name="Cinema1" group-title="Cinema",Cinema One
        """
        fixed_m3u_rows: List = []
        for current_row in m3u_rows:
            new_row = current_row
            if re.match(r"^\s*\"", current_row) and \
                    len(fixed_m3u_rows) > 0 and \
                    m3u.is_extinf_row(fixed_m3u_rows[-1]):
                previous_row = fixed_m3u_rows.pop()
                new_row = previous_row.rstrip() + current_row.lstrip()
            fixed_m3u_rows.append(new_row)
        return fixed_m3u_rows

    @staticmethod
    def _fix_unquoted_numeric_attributes(m3u_rows: List[str]) -> List:
        """
        This covers the case of EXTM3U and EXTINF rows with unquoted numeric attributes.
        Example:
            #EXTINF:-1 tvg-shift=-10.5 group-title="Cinema" tvg-id=22,Channel 22
        """
        unquoted_numbers_regex = r"(?P<attribute_g>\s+(?P<name_g>[\w-]+)=\s*(?P<value_g>-?\d+(:?\.\d+)?))"
        fixed_m3u_rows: List = []
        for current_row in m3u_rows:
            new_row = current_row
            if m3u.is_m3u_header_row(current_row) or m3u.is_extinf_row(current_row):
                for match in re.finditer(unquoted_numbers_regex, current_row):
                    attribute = match.group("attribute_g")
                    name = match.group("name_g")
                    value = match.group("value_g")
                    new_row = new_row.replace(attribute, f" {name}=\"{value}\"")
            fixed_m3u_rows.append(new_row)
        return fixed_m3u_rows

    @staticmethod
    def sanitize(m3u_rows: List) -> List:
        fixed = M3UDoctor._fix_split_quoted_string(m3u_rows)
        fixed = M3UDoctor._fix_unquoted_numeric_attributes(fixed)
        return fixed


class IPTVChannelDoctor:
    @staticmethod
    def _urlencode_value(chan: IPTVChannel, attribute_name: str) -> None:
        """
        This covers the case of tvg-logo attributes not being correctly url-encoded.
        Example (commas in the url):
            tvg-logo="https://some.image.com/images/V1_UX182_CR0,0,182,268_AL_.jpg"
        """
        if attribute_name in chan.attributes:
            value = chan.attributes[attribute_name]
            chan.attributes[attribute_name] = urllib.parse.quote(value, safe=':/%?&=')

    @staticmethod
    def _normalize_attributes_name(chan: IPTVChannel, attribute_name: str) -> None:
        """
        This covers the case of well-known attributes (i.e. the ones in IPTVAttr)
        spelled wrongly.
        Example:
            tvg-ID="" (should be tvg-id="")
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
        """"
        This covers the case of attributes values containing a comma, which can confuse some
        parsing libraries (not this one, though)
        """
        if attribute_name == IPTVAttr.TVG_LOGO.value:
            return
        value: str = chan.attributes[attribute_name]
        if "," in value:
            value = value.replace(",", "_")
            chan.attributes[attribute_name] = value

    @staticmethod
    def sanitize(chan: IPTVChannel) -> IPTVChannel:
        attr: str
        new_chan = chan.copy()
        IPTVChannelDoctor._urlencode_value(new_chan, IPTVAttr.TVG_LOGO.value)
        for attr in chan.attributes.keys():
            IPTVChannelDoctor._convert_commas(new_chan, attr)
            IPTVChannelDoctor._normalize_attributes_name(new_chan, attr)
        return new_chan


class M3UPlaylistDoctor:
    @staticmethod
    def sanitize(playlist: M3UPlaylist):
        """
        This makes sure that all well-known attributes in the playlist are spelled correctly
        and that no commas appear in the attributes value.
        """
        new_playlist: M3UPlaylist = M3UPlaylist()
        chan: IPTVChannel
        for chan in playlist:
            new_playlist.append_channel(IPTVChannelDoctor.sanitize(chan))
        return new_playlist
