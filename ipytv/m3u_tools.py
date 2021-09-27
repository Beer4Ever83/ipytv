#!/usr/env/bin python3
from typing import List

import re

import urllib.parse

from ipytv import M3UPlaylist
from ipytv.channel import IPTVChannel, IPTVAttr


class M3UDoctor:
    @staticmethod
    def fix_split_quoted_string(m3u_rows: List) -> List:
        """
        This covers the case of rows beginning with double quotes that belong to the previous row.
        Example:
            #EXTINF:-1 tvg-id="Cinema1
            " tvg-name="Cinema1" group-title="Cinema",Cinema One
        """
        fixed_m3u_rows: List = []
        lines = len(m3u_rows)
        index: int
        for index in range(lines):
            current_row: str = m3u_rows[index]
            previous_row: str = m3u_rows[index-1]
            if index > 0 and re.match(r"^\s*\"", current_row) and previous_row.startswith("#EXTINF:"):
                fixed_m3u_rows.pop()
                fixed_m3u_rows.append(previous_row.rstrip() + current_row.lstrip())
            else:
                fixed_m3u_rows.append(current_row)
        return fixed_m3u_rows


class IPTVChannelDoctor:
    @staticmethod
    def urlencode_logo(channel: IPTVChannel) -> IPTVChannel:
        """
        This covers the case of tvg-logo attributes not being correctly url-encoded.
        Example (commas in the url):
            tvg-logo="https://some.image.com/images/V1_UX182_CR0,0,182,268_AL_.jpg"
        """
        new_channel = channel.copy()
        logo = new_channel.attributes[IPTVAttr.TVG_LOGO.value]
        new_channel.attributes[IPTVAttr.TVG_LOGO.value] = urllib.parse.quote(logo, safe=':/%')
        return new_channel

    @staticmethod
    def sanitize_attributes(channel: IPTVChannel) -> IPTVChannel:
        """
        This covers the case of well-known attributes (i.e. the ones in IPTVAttr)
        spelled wrongly.
        Example:
            tvg-ID="" (should be tvg-id="")
        """
        attr: str
        new_channel = channel.copy()
        for attr in channel.attributes.keys():
            try:
                IPTVAttr(attr)
            except ValueError:
                try:
                    key = IPTVAttr(attr.lower()).value
                    value = new_channel.attributes[attr]
                    del new_channel.attributes[attr]
                    new_channel.attributes[key] = value
                except ValueError:
                    # It seems not a well-known attribute, so we leave it untouched.
                    pass
        return new_channel


class M3UPlaylistDoctor:
    @staticmethod
    def urlencode_all_logos(playlist: M3UPlaylist):
        """
        This makes sure that all logo URLs in the playlist are encoded correctly.
        """
        index: int
        channel: IPTVChannel
        for index, channel in enumerate(playlist.list):
            playlist.list[index] = IPTVChannelDoctor.urlencode_logo(channel)

    @staticmethod
    def sanitize_all_attributes(playlist: M3UPlaylist):
        """
        This makes sure that all well-known attributes in the playlist are spelled correctly.
        """
        index: int
        channel: IPTVChannel
        for index, channel in playlist.list:
            playlist.list[index] = IPTVChannelDoctor.sanitize_attributes(channel)
