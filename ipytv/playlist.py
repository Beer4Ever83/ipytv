"""Create and handle IPTV playlists.

This module provides functionality for loading, manipulating, and exporting
IPTV playlists in M3U Plus format. It supports loading from various sources
including files, URLs, strings, and JSON format.

Classes:
    M3UPlaylist: Represents an IPTV playlist with channels and attributes

Functions:
    loadl: Load playlist from a list of strings
    loads: Load playlist from a string
    loadf: Load playlist from a file
    loadu: Load playlist from a URL
    loadj: Load playlist from a JSON dictionary
    loadjstr: Load playlist from a JSON string
"""
import json
import logging
import math
import multiprocessing as mp
import re
import typing
from multiprocessing.pool import AsyncResult
from typing import List, Dict, Tuple, Optional, Union, Any

import jsonschema
import requests
from requests import RequestException

import ipytv.channel
from ipytv import m3u
from ipytv.channel import IPTVChannel, IPTVAttr
from ipytv.exceptions import MalformedPlaylistException, URLException, \
    WrongTypeException, IndexOutOfBoundsException, \
    AttributeAlreadyPresentException, AttributeNotFoundException
from ipytv.m3u import M3U_HEADER_TAG

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# The value of __MIN_CHUNK_SIZE cannot be smaller than 2
__MIN_CHUNK_SIZE = 100

# Cache for compiled regex patterns to avoid recompilation
_regex_cache: Dict[Tuple[str, bool], re.Pattern] = {}


def _get_compiled_regex(pattern: str, case_sensitive: bool) -> re.Pattern:
    """Get a compiled regex pattern from cache or compile and cache it.

    Args:
        pattern: The regex pattern string.
        case_sensitive: Whether the pattern should be case-sensitive.

    Returns:
        Compiled regex pattern.
    """
    cache_key = (pattern, case_sensitive)
    if cache_key not in _regex_cache:
        flags = re.RegexFlag(0) if case_sensitive else re.IGNORECASE
        _regex_cache[cache_key] = re.compile(pattern, flags)
    return _regex_cache[cache_key]


class M3UPlaylist:
    """Represents an IPTV playlist in M3U Plus format.

    This class provides comprehensive functionality for managing IPTV playlists,
    including channel manipulation, attribute management, searching, and format
    conversion capabilities.

    Attributes:
        NO_GROUP_KEY: Constant for channels without group assignment
        NO_URL_KEY: Constant for channels without URL assignment
    """
    NO_GROUP_KEY = '_NO_GROUP_'
    NO_URL_KEY = '_NO_URL_'

    def __init__(self) -> None:
        """Initialize an empty M3U playlist."""
        self._channels: List[IPTVChannel] = []
        self._attributes: Dict[str, str] = {}
        self._iter_index: int = -1

    def length(self) -> int:
        """Get the number of channels in the playlist.

        Returns:
            The number of channels in the playlist.

        Example:
            >>> playlist = M3UPlaylist()
            >>> playlist.length()
            0
        """
        return len(self.get_channels()) if self.get_channels() is not None else 0

    def _check_attribute(self, name: str) -> None:
        """Check if an attribute exists, raise exception if not found.

        Args:
            name: The attribute name to check.

        Raises:
            AttributeNotFoundException: If the attribute doesn't exist.
        """
        if name not in self._attributes:
            log.error("the attribute %s does not exist", name)
            raise AttributeNotFoundException(f"the attribute {name} does not exist")

    def get_attribute(self, name: str) -> str:
        """Get the value of a playlist attribute.

        Args:
            name: The name of the attribute to retrieve.

        Returns:
            The value of the specified attribute.

        Raises:
            AttributeNotFoundException: If the attribute doesn't exist.

        Example:
            >>> playlist.add_attribute("url-tvg", "http://example.com/guide.xml")
            >>> playlist.get_attribute("url-tvg")
            'http://example.com/guide.xml'
        """
        self._check_attribute(name)
        return self._attributes[name]

    def get_attributes(self) -> Dict[str, str]:
        """Get all playlist attributes.

        Returns:
            A dictionary containing all playlist attributes.

        Example:
            >>> playlist.get_attributes()
            {'url-tvg': 'http://example.com/guide.xml'}
        """
        return self._attributes

    def add_attribute(self, name: str, value: str) -> None:
        """Add a new attribute to the playlist.

        Args:
            name: The name of the attribute to add.
            value: The value of the attribute.

        Raises:
            AttributeAlreadyPresentException: If the attribute already exists.

        Example:
            >>> playlist.add_attribute("url-tvg", "http://example.com/guide.xml")
        """
        if name not in self.get_attributes():
            self._attributes[str(name)] = str(value)
            log.info("attribute added: %s: %s", name, value)
        else:
            log.error(
                "the attribute %s is already present with value %s",
                name,
                self.get_attribute(name)
            )
            raise AttributeAlreadyPresentException(
                f"the attribute {name} is already present with value {self.get_attribute(name)}"
            )

    def add_attributes(self, attributes: Dict[str, str]) -> None:
        """Add multiple attributes to the playlist.

        Args:
            attributes: Dictionary of attribute name-value pairs to add.

        Raises:
            AttributeAlreadyPresentException: If any attribute already exists.

        Example:
            >>> attrs = {"url-tvg": "http://example.com", "refresh": "3600"}
            >>> playlist.add_attributes(attrs)
        """
        for k, v in attributes.items():
            self.add_attribute(k, v)

    def update_attribute(self, name: str, value: str) -> None:
        """Update the value of an existing attribute.

        Args:
            name: The name of the attribute to update.
            value: The new value for the attribute.

        Raises:
            AttributeNotFoundException: If the attribute doesn't exist.

        Example:
            >>> playlist.update_attribute("refresh", "7200")
        """
        self._check_attribute(name)
        self._attributes[name] = value
        log.info("attribute %s updated to value %s", name, value)

    def remove_attribute(self, name: str) -> str:
        """Remove an attribute from the playlist.

        Args:
            name: The name of the attribute to remove.

        Returns:
            The value of the removed attribute.

        Raises:
            AttributeNotFoundException: If the attribute doesn't exist.

        Example:
            >>> old_value = playlist.remove_attribute("refresh")
        """
        self._check_attribute(name)
        attribute = self.get_attribute(name)
        del self._attributes[name]
        log.info("attribute %s deleted", name)
        return attribute

    def _check_index(self, index: int) -> None:
        """Check if an index is valid for the current playlist.

        Args:
            index: The index to validate.

        Raises:
            IndexOutOfBoundsException: If the index is out of bounds.
        """
        length = self.length()
        if index < 0 or index >= length:
            log.error(
                "the index %s is out of the (0, %s) range",
                str(index),
                str(length)
            )
            raise IndexOutOfBoundsException(f"the index {index} is out of the (0, {length}) range")

    def get_channel(self, index: int) -> IPTVChannel:
        """Get a channel by its index position.

        Args:
            index: The zero-based index of the channel to retrieve.

        Returns:
            The IPTVChannel at the specified index.

        Raises:
            IndexOutOfBoundsException: If the index is out of bounds.

        Example:
            >>> first_channel = playlist.get_channel(0)
        """
        self._check_index(index)
        return self.get_channels()[index]

    def get_channels(self) -> List[IPTVChannel]:
        """Get all channels in the playlist.

        Returns:
            A list of all IPTVChannel objects in the playlist.

        Example:
            >>> channels = playlist.get_channels()
            >>> len(channels)
            42
        """
        return self._channels

    def insert_channel(self, index: int, channel: IPTVChannel) -> None:
        """Insert a channel at a specific position.

        Args:
            index: The position where to insert the channel.
            channel: The IPTVChannel to insert.

        Raises:
            IndexOutOfBoundsException: If the index is out of bounds.

        Example:
            >>> new_channel = IPTVChannel(name="News", url="http://example.com")
            >>> playlist.insert_channel(0, new_channel)
        """
        self._check_index(index)
        self.get_channels().insert(index, channel)
        log.info("channel %s inserted in position %s", channel, index)

    def insert_channels(self, index: int, chan_list: List[IPTVChannel]) -> None:
        """Insert multiple channels at a specific position.

        Args:
            index: The position where to insert the channels.
            chan_list: List of IPTVChannel objects to insert.

        Raises:
            IndexOutOfBoundsException: If the index is out of bounds.

        Example:
            >>> channels = [channel1, channel2, channel3]
            >>> playlist.insert_channels(5, channels)
        """
        self._check_index(index)
        for i in range(len(chan_list), 0, -1):
            self.insert_channel(index, chan_list[i-1])
        log.info("%s channels inserted to the playlist in position %s", len(chan_list), index)

    def append_channel(self, channel: IPTVChannel) -> None:
        """Add a channel to the end of the playlist.

        Args:
            channel: The IPTVChannel to append.

        Example:
            >>> new_channel = IPTVChannel(name="Sports", url="http://example.com")
            >>> playlist.append_channel(new_channel)
        """
        self.get_channels().append(channel)
        log.info("channel added: %s", channel)

    def append_channels(self, chan_list: List[IPTVChannel]) -> None:
        """Add multiple channels to the end of the playlist.

        Args:
            chan_list: List of IPTVChannel objects to append.

        Example:
            >>> channels = [channel1, channel2, channel3]
            >>> playlist.append_channels(channels)
        """
        self._channels += chan_list
        log.info("%s channels appended to the playlist", len(chan_list))

    def update_channel(self, index: int, channel: IPTVChannel) -> None:
        """Replace a channel at a specific position.

        Args:
            index: The position of the channel to replace.
            channel: The new IPTVChannel to place at that position.

        Raises:
            IndexOutOfBoundsException: If the index is out of bounds.

        Example:
            >>> updated_channel = IPTVChannel(name="Updated", url="http://new.com")
            >>> playlist.update_channel(0, updated_channel)
        """
        self._check_index(index)
        self._channels[index] = channel
        log.info("index %s has been updated with channel %s", str(index), channel)

    def remove_channel(self, index: int) -> IPTVChannel:
        """Remove a channel from the playlist.

        Args:
            index: The position of the channel to remove.

        Returns:
            The removed IPTVChannel object.

        Raises:
            IndexOutOfBoundsException: If the index is out of bounds.

        Example:
            >>> removed_channel = playlist.remove_channel(5)
        """
        self._check_index(index)
        channel = self._channels[index]
        del self._channels[index]
        log.info("the channel with index %s has been deleted", str(index))
        return channel

    def _build_header(self) -> str:
        """Build the M3U header with playlist attributes.

        Returns:
            The formatted M3U header string.
        """
        out = M3U_HEADER_TAG
        for k, v in self._attributes.items():
            out += f' {k}="{v}"'
        return out

    def group_by_attribute(self, attribute: str = IPTVAttr.GROUP_TITLE.value,
                           include_no_group: bool = True) -> Dict[str, List[int]]:
        """Group channels by a specific attribute value.

        Args:
            attribute: The attribute name to group by (default: group-title).
            include_no_group: Whether to include channels without the attribute.

        Returns:
            Dictionary mapping attribute values to lists of channel indices.

        Example:
            >>> groups = playlist.group_by_attribute("group-title")
            >>> groups["Sports"]
            [0, 5, 12]  # indices of sports channels
        """
        groups: Dict[str, List[int]] = {}
        for i, chan in enumerate(self.get_channels()):
            group = self.NO_GROUP_KEY
            if attribute in chan.attributes and len(chan.attributes[attribute]) > 0:
                group = chan.attributes[attribute]
            elif not include_no_group:
                continue
            groups.setdefault(group, [])
            groups[group].append(i)
        return groups

    def group_by_url(self, include_no_group: bool = True) -> Dict[str, List[int]]:
        """Group channels by their URL.

        Args:
            include_no_group: Whether to include channels without URLs.

        Returns:
            Dictionary mapping URLs to lists of channel indices.

        Example:
            >>> url_groups = playlist.group_by_url()
            >>> url_groups["http://example.com/stream"]
            [3, 7]  # indices of channels with this URL
        """
        groups: Dict[str, List[int]] = {}
        for i, chan in enumerate(self.get_channels()):
            group = self.NO_URL_KEY
            if len(chan.url) > 0:
                group = chan.url
            elif not include_no_group:
                continue
            groups.setdefault(group, [])
            groups[group].append(i)
        return groups

    @staticmethod
    def _decode_where(where: str) -> Tuple[str, Union[str, None]]:
        """Decode a field specification into main and sub components.

        Args:
            where: Field specification (e.g., "attributes.group-title").

        Returns:
            Tuple of (main_field, sub_field) where sub_field may be None.
        """
        if where is not None:
            where_split = where.split(".")
            where_main = where_split[0]
            where_sub = where_split[1] if len(where_split) > 1 else None
            return where_main, where_sub
        return "", None

    @staticmethod
    def _extract_fields(ch: IPTVChannel) -> List[str]:
        """Extract all searchable field names from a channel.

        Args:
            ch: The channel to extract fields from.

        Returns:
            List of all searchable field specifications.
        """
        out = []
        mains = list(vars(ch))
        for main in mains:
            value = getattr(ch, main)
            if isinstance(value, list):
                for key, _ in enumerate(value):
                    out.append(f"{main}.{key}")
            elif isinstance(value, dict):
                for key, _ in value.items():
                    out.append(f"{main}.{key}")
            else:
                out.append(main)
        return out

    @staticmethod
    def _match_all(ch: IPTVChannel, regex: str, case_sensitive: bool = True) -> bool:
        """Check if any field in a channel matches the regex.

        Args:
            ch: The channel to search in.
            regex: The regular expression to match.
            case_sensitive: Whether matching should be case-sensitive.

        Returns:
            True if any field matches, False otherwise.
        """
        channel_fields = M3UPlaylist._extract_fields(ch)
        compiled_regex = _get_compiled_regex(regex, case_sensitive)
        for field in channel_fields:
            if M3UPlaylist._match_single_compiled(ch, compiled_regex, field):
                return True
        return False

    @staticmethod
    def _match_single(ch: IPTVChannel, regex: str, where: str, case_sensitive: bool = True) -> bool:
        """Check if a specific field in a channel matches the regex.

        Args:
            ch: The channel to search in.
            regex: The regular expression to match.
            where: The field specification to search in.
            case_sensitive: Whether matching should be case-sensitive.

        Returns:
            True if the field matches, False otherwise.
        """
        compiled_regex = _get_compiled_regex(regex, case_sensitive)
        return M3UPlaylist._match_single_compiled(ch, compiled_regex, where)

    @staticmethod
    def _match_single_compiled(ch: IPTVChannel, compiled_regex: re.Pattern, where: str) -> bool:
        """Check if a specific field in a channel matches the compiled regex.

        Args:
            ch: The channel to search in.
            compiled_regex: The compiled regular expression pattern.
            where: The field specification to search in.

        Returns:
            True if the field matches, False otherwise.
        """
        main, sub = M3UPlaylist._decode_where(where)
        if main not in vars(ch):
            return False
        value = getattr(ch, main)
        if sub is not None:
            if isinstance(value, list):
                value = value[int(sub)]
            elif isinstance(value, dict):
                if sub not in value:
                    return False
                value = value[sub]
        return compiled_regex.fullmatch(value) is not None

    def search(
        self,
        regex: str,
        where: Union[Optional[str], List[str]] = None,
        case_sensitive: bool = True
    ) -> List[IPTVChannel]:
        """Search for channels matching a regular expression.

        Searches for channels that have one or more attributes matching the
        specified regex. The match can be done on specific attributes or all
        of them, and can be case-sensitive or not.

        Args:
            regex: Regular expression pattern to match against.
            where: Optional field(s) to search in. If None, it searches all fields.
                   It can be a string like "name" or "attributes.group-title",
                   or a list of such strings.
            case_sensitive: Whether the regex match should be case-sensitive.

        Returns:
            List of IPTVChannel objects matching the search criteria.

        Example:
            >>> # Search for channels with "news" in any field
            >>> news_channels = playlist.search(r".*news.*", case_sensitive=False)
            >>>
            >>> # Search for channels in "Sports" group
            >>> sports = playlist.search(r"Sports", where="attributes.group-title")
            >>>
            >>> # Search in multiple fields
            >>> results = playlist.search(r"HD", where=["name", "attributes.group-title"])
        """
        output_list: List[IPTVChannel] = []
        for ch in self.get_channels():
            if where is None:
                if self._match_all(ch, regex, case_sensitive):
                    output_list.append(ch)
            else:
                if not isinstance(where, list):
                    where = [where]
                for w in where:
                    if self._match_single(ch, regex, w, case_sensitive):
                        output_list.append(ch)
                        # One match is enough
                        break
        return output_list

    def to_m3u_plus_playlist(self) -> str:
        """Convert the playlist to M3U Plus format.

        Returns:
            String representation of the playlist in M3U Plus format.

        Example:
            >>> m3u_content = playlist.to_m3u_plus_playlist()
            >>> print(m3u_content)
            #EXTM3U url-tvg="http://example.com"
            #EXTINF:-1 tvg-id="1",Channel 1
            http://example.com/stream1
        """
        out = f"{self._build_header()}\n"
        for channel in self.get_channels():
            out += channel.to_m3u_plus_playlist_entry()
        return out

    def to_m3u8_playlist(self) -> str:
        """Convert the playlist to standard M3U8 format.

        Returns:
            String representation of the playlist in M3U8 format (without extended attributes).

        Example:
            >>> m3u8_content = playlist.to_m3u8_playlist()
            >>> print(m3u8_content)
            #EXTM3U
            #EXTINF:-1,Channel 1
            http://example.com/stream1
        """
        out = f"{m3u.M3U_HEADER_TAG}\n"
        for channel in self.get_channels():
            out += channel.to_m3u8_playlist_entry()
        return out

    def __to_dict(self) -> Dict[str, Any]:
        """Convert the playlist to a dictionary representation.

        Returns:
            Dictionary containing playlist attributes and channels.
        """
        out = {
            "attributes": self.get_attributes(),
            "channels": [ch.to_dict() for ch in self.get_channels()]
        }
        return out

    def to_json_playlist(self) -> str:
        """Convert the playlist to JSON format.

        Returns:
            JSON string representation of the playlist.

        Example:
            >>> json_data = playlist.to_json_playlist()
            >>> data = json.loads(json_data)
            >>> data["channels"][0]["name"]
            'Channel 1'
        """
        return json.dumps(self.__to_dict())

    def copy(self) -> 'M3UPlaylist':
        """Create a deep copy of the playlist.

        Returns:
            A new M3UPlaylist instance with copied channels and attributes.

        Example:
            >>> playlist_copy = playlist.copy()
            >>> playlist_copy.length() == playlist.length()
            True
        """
        new_pl = M3UPlaylist()
        for channel in self.get_channels():
            new_pl.append_channel(channel.copy())
        new_pl.add_attributes(
            self.get_attributes().copy()     # shallow copy is ok, as we're dealing with primitive types
        )
        return new_pl

    def __eq__(self, other: object) -> bool:
        """Check equality with another playlist.

        Args:
            other: Object to compare with.

        Returns:
            True if playlists are equal, False otherwise.
        """
        length = self.length()
        if not isinstance(other, M3UPlaylist) or \
                other.length() != length:
            return False
        if not other.get_attributes() == self.get_attributes():
            return False
        for i, ch in enumerate(self):
            if not other.get_channel(i) == ch:
                return False
        return True

    def __ne__(self, other: object) -> bool:
        """Check inequality with another playlist.

        Args:
            other: Object to compare with.

        Returns:
            True if playlists are not equal, False otherwise.
        """
        return not self == other

    def __str__(self) -> str:
        """Get string representation of the playlist.

        Returns:
            String representation in M3U Plus format.
        """
        return self.to_m3u_plus_playlist()

    def __iter__(self) -> 'M3UPlaylist':
        """Initialize iteration over channels.

        Returns:
            Self for iteration protocol.
        """
        self._iter_index = 0
        return self

    def __next__(self) -> IPTVChannel:
        """Get next channel in iteration.

        Returns:
            The next IPTVChannel in the playlist.

        Raises:
            StopIteration: When no more channels are available.
        """
        if self._iter_index >= self.length():
            raise StopIteration
        next_chan = self.get_channel(self._iter_index)
        self._iter_index += 1
        return next_chan


# ... rest of the functions remain unchanged ...

def loadl(rows: List[str]) -> 'M3UPlaylist':
    """Load a playlist from a list of strings.

    Parses M3U playlist content from a list of strings, using multiprocessing
    for improved performance on large playlists.

    Args:
        rows: List of strings representing M3U playlist lines.

    Returns:
        A populated M3UPlaylist object.

    Raises:
        WrongTypeException: If rows is not a list.
        MalformedPlaylistException: If playlist format is invalid.

    Example:
        >>> rows = ['#EXTM3U', '#EXTINF:-1,Channel 1', 'http://example.com']
        >>> playlist = loadl(rows)
        >>> playlist.length()
        1
    """
    if not isinstance(rows, List):
        log.error("expected %s, got %s", type([]), type(rows))
        raise WrongTypeException("Wrong type: List expected")
    rows = _remove_blank_rows(rows)
    pl_len = len(rows)
    if pl_len < 1:
        log.error("a playlist should have at least 1 row")
        raise MalformedPlaylistException("a playlist should have at least 1 row")
    header = rows[0].strip()
    if not m3u.is_m3u_header_row(header):
        log.error(
            "the playlist's first row should start with \"%s\", but it's \"%s\"",
            M3U_HEADER_TAG,
            header
        )
        raise MalformedPlaylistException(f"Missing or misplaced {M3U_HEADER_TAG} row")
    out_pl = M3UPlaylist()
    out_pl.add_attributes(_parse_header(header))
    # We're parsing an empty playlist, so we return an empty playlist object
    if pl_len <= 1:
        return out_pl
    cores = mp.cpu_count()
    log.debug("%s cores detected", cores)
    body = rows[1:]
    chunks = _chunk_body(body, cores)
    results: List[AsyncResult] = []
    log.debug("spawning a pool of processes (one per core) to parse the playlist")
    with mp.Pool(processes=cores) as pool:
        for chunk in chunks:
            beginning = chunk["beginning"]
            end = chunk["end"]
            log.debug(
                "assigning a \"populate\" task (beginning: %s, end: %s) to a process in the pool",
                beginning,
                end
            )
            result = pool.apply_async(_populate, (body, beginning, end))
            results.append(result)
        log.debug("closing workers")
        pool.close()
        log.debug("workers closed")
        log.debug("waiting for workers termination")
        pool.join()
        log.debug("workers terminated")
        for result in results:
            p_list = result.get()
            out_pl.append_channels(p_list.get_channels())
    return out_pl


def loads(string: str) -> 'M3UPlaylist':
    """Load a playlist from a string.

    Args:
        string: String containing M3U playlist content.

    Returns:
        A populated M3UPlaylist object.

    Raises:
        WrongTypeException: If string is not a string type.

    Example:
        >>> content = "#EXTM3U\\n#EXTINF:-1,Test\\nhttp://example.com"
        >>> playlist = loads(content)
        >>> playlist.length()
        1
    """
    if isinstance(string, str):
        return loadl(string.split("\n"))
    log.error("expected %s, got %s", type(''), type(string))
    raise WrongTypeException("Wrong type: string expected")


def loadf(filename: str) -> 'M3UPlaylist':
    """Load a playlist from a file.

    Args:
        filename: Path to the M3U file to load.

    Returns:
        A populated M3UPlaylist object.

    Raises:
        WrongTypeException: If filename is not a string.
        FileNotFoundError: If the file doesn't exist.
        IOError: If there's an error reading the file.

    Example:
        >>> playlist = loadf("my_channels.m3u")
        >>> playlist.length()
        150
    """
    if not isinstance(filename, str):
        log.error("expected %s, got %s", type(''), type(filename))
        raise WrongTypeException("Wrong type: string expected")
    with open(filename, encoding='utf-8') as file:
        buffer = file.readlines()
        return loadl(buffer)


def loadu(url: str) -> 'M3UPlaylist':
    """Load a playlist from a URL.

    Args:
        url: URL pointing to an M3U playlist file.

    Returns:
        A populated M3UPlaylist object.

    Raises:
        WrongTypeException: If url is not a string.
        URLException: If there's an error accessing the URL.

    Example:
        >>> playlist = loadu("http://example.com/playlist.m3u")
        >>> playlist.length()
        200
    """
    if not isinstance(url, str):
        log.error("expected %s, got %s", type(''), type(url))
        raise WrongTypeException("Wrong type: string expected")
    try:
        response = requests.get(url, timeout=10)
        if response.ok:
            return loads(response.text)
        raise URLException(
            f"Failure while opening {url}.\nResponse status code: {response.status_code}"
        )
    except RequestException as exception:
        log.error(
            "failure while opening %s: %s",
            url,
            exception
        )
        raise URLException(
            f"Failure while opening {url}.\nError: {exception}"
        ) from exception


def loadj(json_dict: typing.Dict[str, Any]) -> 'M3UPlaylist':
    """Load a playlist from a JSON dictionary.

    Args:
        json_dict: Dictionary containing playlist data in JSON schema format.

    Returns:
        A populated M3UPlaylist object.

    Raises:
        WrongTypeException: If json_dict is not a dictionary or doesn't match schema.

    Example:
        >>> data = {"attributes": {}, "channels": [{"name": "Test", "url": "http://..."}]}
        >>> playlist = loadj(data)
        >>> playlist.length()
        1
    """
    if not isinstance(json_dict, dict):
        log.error("expected %s, got %s", dict, type(json_dict))
        raise WrongTypeException("Wrong type: json dict expected")
    with open("ipytv/resources/schema.json", "r", encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
        try:
            jsonschema.validate(json_dict, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            raise WrongTypeException(f"The input JSON string does not match the expected schema: {e.message}") from e
    pl = M3UPlaylist()
    if "attributes" in json_dict:
        pl.add_attributes(json_dict["attributes"])
    if "channels" in json_dict:
        for json_ch in json_dict["channels"]:
            ch = IPTVChannel(
                url=json_ch["url"],
                name=json_ch["name"],
                duration=json_ch["duration"],
                attributes=json_ch["attributes"],
                extras=json_ch["extras"]
            )
            pl.append_channel(ch)
    return pl


def loadjstr(json_str: str) -> 'M3UPlaylist':
    """Load a playlist from a JSON string.

    Args:
        json_str: String containing JSON-formatted playlist data.

    Returns:
        A populated M3UPlaylist object.

    Raises:
        WrongTypeException: If json_str is not a string or contains invalid JSON.

    Example:
        >>> json_data = '{"attributes": {}, "channels": []}'
        >>> playlist = loadjstr(json_data)
        >>> playlist.length()
        0
    """
    if not isinstance(json_str, str):
        log.error("expected %s, got %s", type(''), type(json_str))
        raise WrongTypeException("Wrong type: string expected")
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        log.error("failure while decoding the JSON string: %s", e)
        raise WrongTypeException("The input string should be a valid JSON string.") from e
    return loadj(data)


def _remove_blank_rows(rows: List[str]) -> List[str]:
    """Remove empty rows from a list of strings.

    Args:
        rows: List of strings that may contain empty rows.

    Returns:
        List of strings with empty rows filtered out.
    """
    new_list = []
    for row in rows:
        if not m3u.is_empty_row(row):
            new_list.append(row)
    return new_list


def _parse_header(header: str) -> Dict[str, str]:
    """Parse M3U header attributes.

    Args:
        header: The M3U header line containing attributes.

    Returns:
        Dictionary of parsed attribute name-value pairs.
    """
    attrs = header.replace(f'{M3U_HEADER_TAG}', '').lstrip()
    attributes = {}
    for attr in attrs.split():
        entry = attr.split("=")
        if len(entry) == 2:
            name = entry[0].replace('"', '')
            value = entry[1].replace('"', '')
            attributes[name] = value
    return attributes


def _build_chunk(beginning: int, end: int) -> Dict[str, int]:
    """Build a chunk specification for multiprocessing.

    Args:
        beginning: Start index of the chunk (inclusive).
        end: End index of the chunk (inclusive).

    Returns:
        Dictionary containing chunk boundaries.
    """
    return {
        "beginning": beginning,
        "end": end
    }


def _find_chunk_end(sub_list: List[str]) -> int:
    """Find the appropriate end point for a processing chunk.

    Args:
        sub_list: List of rows to search for chunk end.

    Returns:
        Offset where the chunk should end.
    """
    for offset, row in enumerate(sub_list):
        if m3u.is_url_row(row):
            log.debug(
                "chunking at the following row (offset %s) as it's a url row:\n%s",
                offset,
                row
            )
            return offset
    return len(sub_list)


def _compute_chunk(rows: List[str], start: int, min_size: int) -> Dict[str, int]:
    """Compute chunk boundaries for multiprocessing.

    Args:
        rows: List of all rows to process.
        start: Starting index for this chunk.
        min_size: Minimum size for the chunk.

    Returns:
        Dictionary containing chunk boundaries.
    """
    length = len(rows)
    if length - start > min_size:
        log.debug(
            "there are enough remaining rows (%s left) to populate at least one full-size chunk",
            length - start
        )
        provisional_end = start + min_size - 1
        sub_list = rows[provisional_end:]
        offset = _find_chunk_end(sub_list)
        final_end = provisional_end + offset
        log.debug("chunk end found at row %s", final_end)
        return _build_chunk(start, final_end)
    log.debug(
        "there are less than (or exactly) %s rows (%s left), so the chunk end is the list end",
        min_size,
        length - start
    )
    return _build_chunk(start, length-1)


def _chunk_body(rows: List[str], chunk_count: int, enforce_min_size: bool = True) -> List[Dict[str, int]]:
    """Split playlist rows into chunks for multiprocessing.

    Args:
        rows: List of playlist rows to chunk.
        chunk_count: Number of chunks to create.
        enforce_min_size: Whether to enforce minimum chunk size.

    Returns:
        List of chunk specifications for parallel processing.
    """
    length = len(rows)
    chunk_size = math.ceil(length / chunk_count)
    if enforce_min_size and chunk_size < __MIN_CHUNK_SIZE:
        log.debug(
            "no chunking as each of the %s chunks would be smaller than the configured minimum (%s < %s)",
            chunk_count,
            chunk_size,
            __MIN_CHUNK_SIZE
        )
        return [
            _build_chunk(0, length - 1)
        ]
    chunk_list = []
    start = 0
    while start < length:
        chunk: Dict[str, int] = _compute_chunk(rows, start, chunk_size)
        chunk_list.append(chunk)
        start = chunk["end"] + 1
    log.debug("chunk_list: %s", chunk_list)
    return chunk_list


def _populate(rows: List[str], beginning: int = 0, end: int = -1) -> 'M3UPlaylist':
    """Populate a playlist from a subset of rows.

    Args:
        rows: List of playlist rows to process.
        beginning: Starting index for processing.
        end: Ending index for processing.

    Returns:
        A populated M3UPlaylist with channels from the specified range.
    """
    p_list = M3UPlaylist()
    if end == -1:
        end = len(rows) - 1
    log.debug("populating playlist with rows from %s to %s", beginning, end)
    entry = []
    previous_row = rows[beginning]
    if m3u.is_comment_or_tag_row(previous_row) or m3u.is_url_row(previous_row):
        entry.append(rows[beginning])
        log.debug("chunk starting with a url, comment or tag row")
    if m3u.is_url_row(previous_row):
        _append_entry(entry, p_list)
        entry = []
        log.debug("adding entry to the playlist: %s", entry)
    for row in rows[beginning + 1: end + 1]:
        row = row.strip()
        log.debug("parsing row: %s", row)
        if m3u.is_extinf_row(row):
            if m3u.is_extinf_row(previous_row):
                log.warning("adjacent #EXTINF rows detected")
                _append_entry(entry, p_list)
                log.debug("adding entry to the playlist: %s", entry)
                entry = []
            entry.append(row)
        elif m3u.is_comment_or_tag_row(row):
            entry.append(row)
            log.warning("commented row or unsupported tag found:\n%s", row)
        elif m3u.is_url_row(row):
            entry.append(row)
            log.debug("adding entry to the playlist: %s", entry)
            _append_entry(entry, p_list)
            entry = []
        previous_row = row
    return p_list


def _append_entry(entry: List[str], pl: M3UPlaylist) -> None:
    """Append a playlist entry to a playlist.

    Args:
        entry: List of strings representing a complete playlist entry.
        pl: The M3UPlaylist to append the entry to.
    """
    channel = ipytv.channel.from_playlist_entry(entry)
    pl.append_channel(channel)


if __name__ == "__main__":
    pass
