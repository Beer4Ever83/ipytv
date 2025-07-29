"""Everything related with the parsing of M3U Plus files

This module provides functions for parsing and validating M3U and M3U Plus playlist formats.
It handles both well-formed and malformed EXTINF rows with various attribute formats.

Constants:
    M3U_HEADER_TAG: The standard M3U header identifier "#EXTM3U"
"""
import re
from typing import Optional, Dict

M3U_HEADER_TAG = "#EXTM3U"

# Pre-compiled regular expressions for better performance
_M3U_EXTINF_PATTERN = re.compile(r'^#EXTINF:[-0-9\.]+,.*$')
_M3U_PLUS_EXTINF_PATTERN = re.compile(r'^#EXTINF:[-0-9\.]+(\s+[\w-]+="[^"]*")+,.*$')
_M3U_PLUS_EXTINF_PARSE_PATTERN = re.compile(
    r'^#EXTINF:(?P<duration_g>[-0-9\.]+)'
    r'(?P<attributes_g>(\s+[\w-]+="[^"]*")*),'
    r'(?P<name_g>.*)'
)
_M3U_PLUS_BROKEN_EXTINF_PARSE_PATTERN = re.compile(
    r'^#EXTINF:(?P<duration_g>[-0-9\.]+)'
    r'(?P<attributes_g>(\s+[\w-]+=".*)*),'
    r'(?P<name_g>.*)'
)
_M3U_PLUS_BROKEN_ATTRIBUTE_PARSE_PATTERN = re.compile(r'(?:\s+)[\w-]+="')


def is_m3u_header_row(row: str) -> bool:
    """Check if a row is an M3U header row.

    Args:
        row: The string row to check.

    Returns:
        True if the row starts with the M3U header tag, False otherwise.

    Example:
        >>> is_m3u_header_row("#EXTM3U")
        True
        >>> is_m3u_header_row("#EXTINF:-1,Channel")
        False
    """
    return row.startswith(M3U_HEADER_TAG)


def is_m3u_extinf_row(row: str) -> bool:
    """Check if a row is a standard M3U EXTINF row.

    Args:
        row: The string row to check.

    Returns:
        True if the row matches the standard M3U EXTINF format, False otherwise.

    Example:
        >>> is_m3u_extinf_row("#EXTINF:-1,Channel Name")
        True
        >>> is_m3u_extinf_row("#EXTINF:-1 tvg-id=\"1\",Channel")
        False
    """
    return _M3U_EXTINF_PATTERN.search(row) is not None


def is_m3u_plus_extinf_row(row: str) -> bool:
    """Check if a row is an M3U Plus EXTINF row with attributes.

    Args:
        row: The string row to check.

    Returns:
        True if the row matches the M3U Plus EXTINF format with attributes, False otherwise.

    Example:
        >>> is_m3u_plus_extinf_row('#EXTINF:-1 tvg-id="1" group-title="News",Channel')
        True
        >>> is_m3u_plus_extinf_row("#EXTINF:-1,Channel Name")
        False
    """
    return _M3U_PLUS_EXTINF_PATTERN.search(row) is not None


def match_m3u_plus_broken_extinf_row(row: str) -> Optional[re.Match]:
    """Match an M3U Plus EXTINF row that may have malformed attributes.

    This function is designed to handle EXTINF rows where attribute values
    contain improperly escaped quotes or other formatting issues.

    Args:
        row: The string row to match.

    Returns:
        A regex match object if the row matches the broken EXTINF pattern,
        None otherwise.

    Example:
        >>> match = match_m3u_plus_broken_extinf_row('#EXTINF:-1 title="Show "Part 1"",Channel')
        >>> match is not None
        True
    """
    return _M3U_PLUS_BROKEN_EXTINF_PARSE_PATTERN.search(row)


def get_m3u_plus_broken_attributes(row: str) -> Dict[str, str]:
    """Extract attributes from a malformed M3U Plus EXTINF row.

    Parses EXTINF rows with "broken" attributes where values contain
    badly nested double quotes. The function:
    1. Extracts the attribute list from the row
    2. Finds attribute name patterns
    3. Splits and extracts attribute values
    4. Replaces misplaced quotes with underscores

    Args:
        row: The malformed EXTINF row string to parse.

    Returns:
        A dictionary mapping attribute names to their cleaned values.
        It returns an empty dict if the row doesn't match the expected pattern.

    Example:
        >>> attrs = get_m3u_plus_broken_attributes('#EXTINF:-1 title="Show "Part 1"",Channel')
        >>> attrs['title']
        'Show _Part 1_'
    """
    match = match_m3u_plus_broken_extinf_row(row)
    if match is None:
        return {}
    attributes = match.group("attributes_g").rstrip(',')
    tokens = _M3U_PLUS_BROKEN_ATTRIBUTE_PARSE_PATTERN.findall(attributes)
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
    """Match a well-formed M3U Plus EXTINF row.

    Args:
        row: The string row to match.

    Returns:
        A regex match object with named groups (duration_g, attributes_g, name_g)
        if the row matches, None otherwise.

    Example:
        >>> match = match_m3u_plus_extinf_row('#EXTINF:-1 tvg-id="1",Channel')
        >>> match.group('name_g')
        'Channel'
    """
    return _M3U_PLUS_EXTINF_PARSE_PATTERN.match(row)


def is_extinf_row(row: str) -> bool:
    """Check if a row is any type of EXTINF row.

    Args:
        row: The string row to check.

    Returns:
        True if the row starts with "#EXTINF", False otherwise.

    Example:
        >>> is_extinf_row("#EXTINF:-1,Channel")
        True
        >>> is_extinf_row("#EXTM3U")
        False
    """
    return row.startswith("#EXTINF")


def is_comment_or_tag_row(row: str) -> bool:
    """Check if a row is a comment or tag row.

    Args:
        row: The string row to check.

    Returns:
        True if the row starts with '#', False otherwise.

    Example:
        >>> is_comment_or_tag_row("#EXTM3U")
        True
        >>> is_comment_or_tag_row("http://example.com/stream")
        False
    """
    return row.startswith('#')


def is_empty_row(row: str) -> bool:
    """Check if a row is empty or contains only whitespace.

    Args:
        row: The string row to check.

    Returns:
        True if the row is empty or whitespace-only, False otherwise.

    Example:
        >>> is_empty_row("   ")
        True
        >>> is_empty_row("http://example.com")
        False
    """
    return not row.strip()


def is_url_row(row: str) -> bool:
    """Check if a row contains a URL (not a header, comment, tag, or empty row).

    Args:
        row: The string row to check.

    Returns:
        True if the row appears to be a URL, False otherwise.

    Example:
        >>> is_url_row("http://example.com/stream.m3u8")
        True
        >>> is_url_row("#EXTINF:-1,Channel")
        False
    """
    return not is_m3u_header_row(row) and not is_comment_or_tag_row(row) and not is_empty_row(row)


if __name__ == "__main__":
    pass
