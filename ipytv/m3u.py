import re
from typing import Optional

M3U_HEADER_TAG = "#EXTM3U"
M3U_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+,.*$'
M3U_PLUS_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+(\s+[\w-]+="[^"]*")+,.*$'
M3U_PLUS_EXTINF_PARSE_REGEX = r'^#EXTINF:(?P<duration_g>[-0-9\.]+)' \
                                r'(?P<attributes_g>(\s+[\w-]+="[^"]*")*),' \
                                r'(?P<name_g>.*)'


def is_m3u_header_row(row: str) -> bool:
    return row.startswith(M3U_HEADER_TAG)


def is_m3u_extinf_row(row: str) -> bool:
    return re.search(M3U_EXTINF_REGEX, row) is not None


def is_m3u_plus_extinf_row(row: str) -> bool:
    return re.search(M3U_PLUS_EXTINF_REGEX, row) is not None


def match_m3u_plus_extinf_row(row: str) -> Optional[re.Match]:
    return re.match(M3U_PLUS_EXTINF_PARSE_REGEX, row)


def is_extinf_row(row: str) -> bool:
    return row.startswith("#EXTINF")


def is_comment_or_tag_row(row: str) -> bool:
    return row.startswith('#')
