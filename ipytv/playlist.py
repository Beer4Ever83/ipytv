"""Create and handle IPTV playlists

Classes:
    M3UPlaylist

Functions:
    loadl
    loads
    loadf
    loadu

"""
import logging
import math
import multiprocessing as mp
import re
from multiprocessing.pool import AsyncResult
from typing import List, Dict, Tuple, Optional, Union

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


class M3UPlaylist:
    """
    A class that represents an IPTV playlist in M3U Plus format

    Methods
    ----------
    length() -> int
        Returns how many channels the playlist contains
    get_attribute(name: str) -> str
        Returns the value of the "name" playlist attribute. It throws AttributeNotFoundException if the attribute is not
        found.
    get_attributes() -> Dict[str, str]
        Returns a dictionary with all the playlist attributes
    add_attribute(name: str, value: str) -> None
        Adds the attribute "name" with value "value" to the playlist. It throws AttributeAlreadyPresentException if the
        attribute already exists
    add_attributes(attributes: Dict[str, str]) -> None
        Adds multiple attributes at once
    update_attribute(name: str, value: str) -> None:
        Change the value of an already existing attribute. It throws AttributeNotFoundException if the attribute is not
        found
    remove_attribute(name: str) -> str:
        Removes the specified attribute. It throws AttributeNotFoundException if the attribute is not found
    get_channel(index: int) -> IPTVChannel:

    get_channels(self) -> List[IPTVChannel]:

    insert_channel(index: int, channel: IPTVChannel) -> None:

    insert_channels(index: int, chan_list: List[IPTVChannel]) -> None:

    append_channel(channel: IPTVChannel) -> None:

    append_channels(chan_list: List[IPTVChannel]) -> None:

    update_channel(index: int, channel: IPTVChannel) -> None:

    remove_channel(index: int) -> IPTVChannel:

    group_by_attribute(attribute: str = IPTVAttr.GROUP_TITLE.value,

    group_by_url(include_no_group: bool = True) -> Dict:

    to_m3u_plus_playlist(self) -> str:

    to_m3u8_playlist(self) -> str:

    copy(self) -> 'M3UPlaylist':

    """
    NO_GROUP_KEY = '_NO_GROUP_'
    NO_URL_KEY = '_NO_URL_'

    def __init__(self):
        self._channels: List[IPTVChannel] = []
        self._attributes: Dict[str, str] = {}
        self._iter_index: int = -1

    def length(self) -> int:
        return len(self.get_channels()) if self.get_channels() is not None else 0

    def _check_attribute(self, name: str) -> None:
        if name not in self._attributes:
            log.error("the attribute %s does not exist", name)
            raise AttributeNotFoundException(f"the attribute {name} does not exist")

    def get_attribute(self, name: str) -> str:
        self._check_attribute(name)
        return self._attributes[name]

    def get_attributes(self) -> Dict[str, str]:
        return self._attributes

    def add_attribute(self, name: str, value: str) -> None:
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
        for k, v in attributes.items():
            self.add_attribute(k, v)

    def update_attribute(self, name: str, value: str) -> None:
        self._check_attribute(name)
        self._attributes[name] = value
        log.info("attribute %s updated to value %s", name, value)

    def remove_attribute(self, name: str) -> str:
        self._check_attribute(name)
        attribute = self.get_attribute(name)
        del self._attributes[name]
        log.info("attribute %s deleted", name)
        return attribute

    def _check_index(self, index: int) -> None:
        length = self.length()
        if index < 0 or index >= length:
            log.error(
                "the index %s is out of the (0, %s) range",
                str(index),
                str(length)
            )
            raise IndexOutOfBoundsException(f"the index {index} is out of the (0, {length}) range")

    def get_channel(self, index: int) -> IPTVChannel:
        self._check_index(index)
        return self.get_channels()[index]

    def get_channels(self) -> List[IPTVChannel]:
        return self._channels

    def insert_channel(self, index: int, channel: IPTVChannel) -> None:
        self._check_index(index)
        self.get_channels().insert(index, channel)
        log.info("channel %s inserted in position %s", channel, index)

    def insert_channels(self, index: int, chan_list: List[IPTVChannel]) -> None:
        self._check_index(index)
        for i in range(len(chan_list), 0, -1):
            self.insert_channel(index, chan_list[i])
        log.info("%s channels inserted to the playlist in position %s", len(chan_list), index)

    def append_channel(self, channel: IPTVChannel) -> None:
        self.get_channels().append(channel)
        log.info("channel added: %s", channel)

    def append_channels(self, chan_list: List[IPTVChannel]) -> None:
        self._channels += chan_list
        log.info("%s channels appended to the playlist", len(chan_list))

    def update_channel(self, index: int, channel: IPTVChannel) -> None:
        self._check_index(index)
        self._channels[index] = channel
        log.info("index %s has been updated with channel %s", str(index), channel)

    def remove_channel(self, index: int) -> IPTVChannel:
        self._check_index(index)
        channel = self._channels[index]
        del self._channels[index]
        log.info("the channel with index %s has been deleted", str(index))
        return channel

    def _build_header(self) -> str:
        out = M3U_HEADER_TAG
        for k, v in self._attributes.items():
            out += f' {k}="{v}"'
        return out

    def group_by_attribute(self, attribute: str = IPTVAttr.GROUP_TITLE.value,
                           include_no_group: bool = True) -> Dict:
        groups: Dict[str, List] = {}
        for i, chan in enumerate(self.get_channels()):
            group = self.NO_GROUP_KEY
            if attribute in chan.attributes and len(chan.attributes[attribute]) > 0:
                group = chan.attributes[attribute]
            elif not include_no_group:
                continue
            groups.setdefault(group, [])
            groups[group].append(i)
        return groups

    def group_by_url(self, include_no_group: bool = True) -> Dict[str, List]:
        groups: Dict[str, List] = {}
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
        if where is not None:
            where_split = where.split(".")
            where_main = where_split[0]
            where_sub = where_split[1] if len(where_split) > 1 else None
            return where_main, where_sub
        return "", None

    @staticmethod
    def _extract_fields(ch: IPTVChannel) -> List[str]:
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
        channel_fields = M3UPlaylist._extract_fields(ch)
        for field in channel_fields:
            if M3UPlaylist._match_single(ch, regex, field, case_sensitive=case_sensitive):
                return True
        return False

    @staticmethod
    def _match_single(ch: IPTVChannel, regex: str, where: str, case_sensitive: bool = True) -> bool:
        flags: re.RegexFlag = re.IGNORECASE if case_sensitive is False else re.RegexFlag(0)
        main, sub = M3UPlaylist._decode_where(where)
        value = getattr(ch, main)
        if sub is not None:
            if isinstance(value, list):
                value = value[int(sub)]
            elif isinstance(value, dict):
                value = value[sub]
        if re.fullmatch(regex, value, flags=flags) is None:
            return False
        return True

    def search(self, regex: str, where: Union[Optional[str], List[str]] = None, case_sensitive: bool = True) -> List[IPTVChannel]:
        """
        .. py:method:: search

        Searches for channels that have one or more attributes matching the
        specified regex. The match can be done on a specific set of attributes
        or on all of them and the comparison can be made in a case-sensitive
        fashion or not. The method returns a list of matching IPTVChannel
        objects.

        :param  regex:  All channels matching this regular expression will be
                        appended to the output list.
        :type   regex:  str
        :param  where:  Optional. The attribute(s) to match the regex against.
                        Omit this (or set it to None) to search in all
                        attributes.
        :type   where:  str or list[str] or None
        :param  case_sensitive: Optional. This flag controls whether the regex
                                match shall be done in a case-sensitive fashion
                                or not.
        :type   case_sensitive: bool

        :return:    a list of IPTVChannel objects one or more attributes of
                    which match the search pattern.
        :rtype:     List[IPTVChannel]
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
        return output_list

    def to_m3u_plus_playlist(self) -> str:
        out = f"{self._build_header()}\n"
        for channel in self.get_channels():
            out += channel.to_m3u_plus_playlist_entry()
        return out

    def to_m3u8_playlist(self) -> str:
        out = f"{m3u.M3U_HEADER_TAG}\n"
        for channel in self.get_channels():
            out += channel.to_m3u8_playlist_entry()
        return out

    def copy(self) -> 'M3UPlaylist':
        new_pl = M3UPlaylist()
        for channel in self.get_channels():
            new_pl.append_channel(channel.copy())
        new_pl.add_attributes(
            self.get_attributes().copy()     # shallow copy is ok, as we're dealing with primitive types
        )
        return new_pl

    def __eq__(self, other: object) -> bool:
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
        return not self == other

    def __str__(self) -> str:
        return self.to_m3u_plus_playlist()

    def __iter__(self) -> 'M3UPlaylist':
        self._iter_index = 0
        return self

    def __next__(self) -> IPTVChannel:
        if self._iter_index >= self.length():
            raise StopIteration
        next_chan = self.get_channel(self._iter_index)
        self._iter_index += 1
        return next_chan


def loadl(rows: List) -> 'M3UPlaylist':
    if not isinstance(rows, List):
        log.error("expected %s, got %s", type([]), type(rows))
        raise WrongTypeException("Wrong type: List expected")
    if len(rows) < 2:
        log.error("a playlist should have at least 2 rows (found %s)", len(rows))
        raise MalformedPlaylistException(f"a playlist should have at least 2 rows (found {len(rows)})")
    rows = _remove_blank_rows(rows)
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
    if isinstance(string, str):
        return loadl(string.split("\n"))
    log.error("expected %s, got %s", type(''), type(string))
    raise WrongTypeException("Wrong type: string expected")


def loadf(filename: str) -> 'M3UPlaylist':
    if not isinstance(filename, str):
        log.error("expected %s, got %s", type(''), type(filename))
        raise WrongTypeException("Wrong type: string expected")
    with open(filename, encoding='utf-8') as file:
        buffer = file.readlines()
        return loadl(buffer)


def loadu(url: str) -> 'M3UPlaylist':
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


def _remove_blank_rows(rows: List[str]) -> List[str]:
    new_list = []
    for row in rows:
        if not m3u.is_empty_row(row):
            new_list.append(row)
    return new_list


def _parse_header(header: str) -> Dict[str, str]:
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
    return {
        # beginning is the index of the first element of the current chunk (element included)
        "beginning": beginning,
        # end is the index of the last element of the current chunk (element included)
        "end": end
    }


def _find_chunk_end(sub_list: List[str]) -> int:
    for offset, row in enumerate(sub_list):
        if m3u.is_url_row(row):
            log.debug(
                "chunking at the following row (offset %s) as it's a url row:\n%s",
                offset,
                row
            )
            return offset
    # offset is the position relative to sub_list where the first url row has been found
    return len(sub_list)


def _compute_chunk(rows: List, start: int, min_size: int) -> Dict[str, int]:
    length = len(rows)
    if length - start > min_size:
        log.debug(
            "there are enough remaining rows (%s left) to populate at least one full-size chunk",
            length - start
        )
        provisional_end = start + min_size - 1
        # sub_list's first element is potentially the last element of the chunk, but only if it's a url row
        sub_list = rows[provisional_end:]
        # Let's grow the current chunk until the first url row
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


def _chunk_body(rows: List, chunk_count: int, enforce_min_size: bool = True) -> List:
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


def _populate(rows: List, beginning: int = 0, end: int = -1) -> 'M3UPlaylist':
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
                # case of two adjacent #EXTINF rows, so a url-less entry is
                # added. This shouldn't be allowed, but sometimes those #EXTINF
                # rows are used as group separators.
                log.warning("adjacent #EXTINF rows detected")
                _append_entry(entry, p_list)
                log.debug("adding entry to the playlist: %s", entry)
                entry = []
            entry.append(row)
        elif m3u.is_comment_or_tag_row(row):
            # case of a row with a non-supported tag or a comment, so it's copied as-is
            entry.append(row)
            log.warning("commented row or unsupported tag found:\n%s", row)
        elif m3u.is_url_row(row):
            # case of a plain url row (regardless if preceded by an #EXTINF row or not)
            entry.append(row)
            log.debug("adding entry to the playlist: %s", entry)
            _append_entry(entry, p_list)
            entry = []
        previous_row = row
    return p_list


def _append_entry(entry: List, pl: M3UPlaylist):
    channel = ipytv.channel.from_playlist_entry(entry)
    pl.append_channel(channel)
