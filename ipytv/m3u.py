"""Everything related with the parsing of M3U Plus files

Functions:
    is_m3u_header_row
    is_m3u_extinf_row
    is_m3u_plus_extinf_row
    match_m3u_plus_broken_extinf_row
    get_m3u_plus_broken_attributes
    match_m3u_plus_extinf_row
    is_extinf_row
    is_comment_or_tag_row
    is_url_row

Constants:
    M3U_HEADER_TAG
"""
import re
from typing import Optional, Dict

M3U_HEADER_TAG = "#EXTM3U"
__M3U_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+,.*$'
__M3U_PLUS_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+(\s+[\w-]+="[^"]*")+,.*$'
__M3U_PLUS_EXTINF_PARSE_REGEX = r'^#EXTINF:(?P<duration_g>[-0-9\.]+)' \
    r'(?P<attributes_g>(\s+[\w-]+="[^"]*")*),' \
    r'(?P<name_g>.*)'
__M3U_PLUS_BROKEN_EXTINF_PARSE_REGEX = r'^#EXTINF:(?P<duration_g>[-0-9\.]+)' \
    r'(?P<attributes_g>(\s+[\w-]+=".*)*),' \
    r'(?P<name_g>.*)'
__M3U_PLUS_BROKEN_ATTRIBUTE_PARSE_REGEX = r'(?:\s+)[\w-]+="'


def is_m3u_header_row(row: str) -> bool:
    return row.startswith(M3U_HEADER_TAG)


def is_m3u_extinf_row(row: str) -> bool:
    return re.search(__M3U_EXTINF_REGEX, row) is not None


def is_m3u_plus_extinf_row(row: str) -> bool:
    return re.search(__M3U_PLUS_EXTINF_REGEX, row) is not None


def match_m3u_plus_broken_extinf_row(row: str) -> Optional[re.Match]:
    return re.search(__M3U_PLUS_BROKEN_EXTINF_PARSE_REGEX, row)


def get_m3u_plus_broken_attributes(row: str) -> Dict[str, str]:
    """In the case of an EXTINF row with a list of "broken" attributes (i.e.
    attributes the value of which contains badly nested double quotes), this
    function can parse the list of attributes by:
    1. Extracting only the attribute list from the whole row (please note: the
    leading space is kept, but the trailing comma is removed).
    2. Finding all occurrences of the attribute-name=" pattern and extracting
    the attribute name from the results.
    3. Looping through all the attribute patterns and splitting the whole row in
    two, using the attribute name as separator, and taking the right part of the
    split.
    4. Splitting the right part in two, by using next attribute as separator:
    the wanted value will be found in the left part of the split.
    5. Replacing all misplaced double quotes with underscores.
    """
    match = match_m3u_plus_broken_extinf_row(row)
    if match is None:
        return {}
    attributes = match.group("attributes_g").rstrip(',')
    tokens = re.findall(__M3U_PLUS_BROKEN_ATTRIBUTE_PARSE_REGEX, attributes)
    attrs = {}
    for i, token in enumerate(tokens):
        name = token.lstrip().rstrip('="')
        right = row.split(token)[1]
        separator = tokens[i+1] if i < len(tokens)-1 else '",'
        left = right.split(separator)[0].rstrip('"')
        # Let's replace misplaced double quotes with underscore
        attrs[name] = left.replace('"', '_')
    return attrs


def match_m3u_plus_extinf_row(row: str) -> Optional[re.Match]:
    return re.match(__M3U_PLUS_EXTINF_PARSE_REGEX, row)


def is_extinf_row(row: str) -> bool:
    return row.startswith("#EXTINF")


def is_comment_or_tag_row(row: str) -> bool:
    return row.startswith('#')


def is_empty_row(row: str) -> bool:
    return len(row.strip()) == 0


def is_url_row(row: str) -> bool:
    return not is_m3u_header_row(row) and not is_comment_or_tag_row(row) and not is_empty_row(row)
