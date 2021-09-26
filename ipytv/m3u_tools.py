#!/usr/env/bin python3
from typing import List

import re

import urllib.parse

from ipytv import M3UPlaylist
from ipytv.channel import IPTVChannel, IPTVAttr


class M3UFileDoctor:
    @staticmethod
    def fix_split_quoted_string(infile: str, outfile: str):
        with open(infile, encoding='utf-8') as file:
            m3u_rows = file.readlines()
        output_str = "".join(M3UDoctor.fix_split_quoted_string(m3u_rows))
        with open(outfile, "w", encoding='utf-8') as file:
            file.write(output_str)


class M3UDoctor:
    """
    This covers the case of rows beginning with double quotes that belong to the previous row.
    Example:
        #EXTINF:-1 tvg-id="Cinema1
        " tvg-name="Cinema1" group-title="Cinema",Cinema One
    """
    @staticmethod
    def fix_split_quoted_string(m3u_rows: List) -> List:
        lines = len(m3u_rows)
        for index in range(lines):
            if re.match("^[[:space:]]*\"", m3u_rows[index]):
                m3u_rows[index] = m3u_rows[index].replace("\"", "", 1)
                m3u_rows[index - 1] = m3u_rows[index - 1].rstrip() + "\""
        return m3u_rows


class IPTVChannelDoctor:
    """
    This covers the case of tvg-logo attributes not being correctly url-encoded.
    Example (commas in the url):
        tvg-logo="https://some.image.com/images/V1_UX182_CR0,0,182,268_AL_.jpg"
    """
    @staticmethod
    def urlencode_logo(channel: IPTVChannel) -> IPTVChannel:
        logo = channel.attributes[IPTVAttr.TVG_LOGO.value]
        channel.attributes[IPTVAttr.TVG_LOGO.value] = urllib.parse.quote(logo, safe=':/%')
        return channel


class M3UPlaylistDoctor:
    """
    This makes sure that all logo URLs in the playlist are encoded correctly.
    """
    @staticmethod
    def urlencode_logos(playlist: M3UPlaylist):
        channel: IPTVChannel
        for channel in playlist.list:
            IPTVChannelDoctor.urlencode_logo(channel)
