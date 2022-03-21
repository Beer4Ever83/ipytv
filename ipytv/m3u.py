import re
from typing import Optional, Dict

M3U_HEADER_TAG = "#EXTM3U"
M3U_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+,.*$'
M3U_PLUS_EXTINF_REGEX = r'^#EXTINF:[-0-9\.]+(\s+[\w-]+="[^"]*")+,.*$'
M3U_PLUS_EXTINF_PARSE_REGEX = r'^#EXTINF:(?P<duration_g>[-0-9\.]+)' \
    r'(?P<attributes_g>(\s+[\w-]+="[^"]*")*),' \
    r'(?P<name_g>.*)'
M3U_PLUS_BROKEN_EXTINF_PARSE_REGEX = r'^#EXTINF:(?P<duration_g>[-0-9\.]+)' \
    r'(?P<attributes_g>(\s+[\w-]+=".*)*),' \
    r'(?P<name_g>.*)'
M3U_PLUS_BROKEN_ATTRIBUTE_PARSE_REGEX = r'(?:\s+)[\w-]+="'


def is_m3u_header_row(row: str) -> bool:
    return row.startswith(M3U_HEADER_TAG)


def is_m3u_extinf_row(row: str) -> bool:
    return re.search(M3U_EXTINF_REGEX, row) is not None


def is_m3u_plus_extinf_row(row: str) -> bool:
    return re.search(M3U_PLUS_EXTINF_REGEX, row) is not None


def match_m3u_plus_broken_extinf_row(row: str) -> Optional[re.Match]:
    return re.search(M3U_PLUS_BROKEN_EXTINF_PARSE_REGEX, row)


def get_m3u_plus_broken_attributes(row: str) -> Dict[str, str]:
    """In the case of an EXTINF row with a list of "broken" attributes (i.e.
    attributes the value of which contains badly nested dohble quotes), this
    function can parse the list of attributes by:
    1. extract only the attribute list from the whole row (please note: the
    leading space is kept, but the trailing comma is removed);
    2. find all occurrences of the attribute-name=" pattern and extract the
    attribute name from the results;
    3. loop through all the attribute patterns and split the whole row in two
    using the attribute name as separator, and take the right part of the split.
    4. Split the right part in two, by using next attribute as separator: the
    wanted value will be found in the left part of the split.
    5. Replace all double quotes with underscores.
    """
    match = match_m3u_plus_broken_extinf_row(row)
    if match is None:
        return {}
    attributes = match.group("attributes_g").rstrip(',')
    tokens = re.findall(M3U_PLUS_BROKEN_ATTRIBUTE_PARSE_REGEX, attributes)
    attrs = {}
    for i, token in enumerate(tokens):
        name = token.lstrip().rstrip('="')
        right = row.split(token)[1]
        separator = tokens[i+1] if i < len(tokens)-1 else '",'
        left = right.split(separator)[0].rstrip('"')
        # Let's replace double quotes with underscore
        attrs[name] = left.replace('"', '_')
    return attrs


def match_m3u_plus_extinf_row(row: str) -> Optional[re.Match]:
    return re.match(M3U_PLUS_EXTINF_PARSE_REGEX, row)


def is_extinf_row(row: str) -> bool:
    return row.startswith("#EXTINF")


def is_comment_or_tag_row(row: str) -> bool:
    return row.startswith('#')


def is_url_row(row: str) -> bool:
    return not is_comment_or_tag_row(row)
