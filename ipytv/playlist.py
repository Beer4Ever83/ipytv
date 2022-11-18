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
from multiprocessing.pool import AsyncResult
from typing import List, Dict

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
    NO_GROUP_KEY = '_NO_GROUP_'
    NO_URL_KEY = '_NO_URL_'

    def __init__(self):
        self._channels: List[IPTVChannel] = []
        self._attributes: Dict = {}
        self._iter_index: int = -1

    def length(self):
        return len(self._channels) if self._channels is not None else 0

    def _check_attribute(self, name: str) -> None:
        if name not in self._attributes:
            log.error("the attribute %s does not exist", name)
            raise AttributeNotFoundException(f"the attribute {name} does not exist")

    def get_attribute(self, name: str) -> str:
        self._check_attribute(name)
        return self._attributes[name]

    def get_attributes(self) -> Dict:
        return self._attributes

    def add_attribute(self, name: str, value: str) -> None:
        if name not in self._attributes:
            self._attributes[str(name)] = str(value)
            log.info("attribute added: %s: %s", name, value)
        else:
            log.error(
                "the attribute %s is already present with value %s",
                name,
                self._attributes[name]
            )
            raise AttributeAlreadyPresentException(
                f"the attribute {name} is already present with value {self._attributes[name]}"
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
        attribute = self._attributes[name]
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
        return self._channels[index]

    def get_channels(self) -> List[IPTVChannel]:
        return self._channels

    def insert_channel(self, index: int, channel: IPTVChannel) -> None:
        self._check_index(index)
        self._channels.insert(index, channel)
        log.info("channel %s inserted in position %s", channel, index)

    def insert_channels(self, index: int, chan_list: List[IPTVChannel]) -> None:
        self._check_index(index)
        for i in range(len(chan_list), 0, -1):
            self.insert_channel(index, chan_list[i])
        log.info("%s channels inserted to the playlist in position %s", len(chan_list), index)

    def append_channel(self, channel: IPTVChannel) -> None:
        self._channels.append(channel)
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
        for i, chan in enumerate(self._channels):
            group = self.NO_GROUP_KEY
            if attribute in chan.attributes and len(chan.attributes[attribute]) > 0:
                group = chan.attributes[attribute]
            elif not include_no_group:
                continue
            groups.setdefault(group, [])
            groups[group].append(i)
        return groups

    def group_by_url(self, include_no_group: bool = True) -> Dict:
        groups: Dict[str, List] = {}
        for i, chan in enumerate(self._channels):
            group = self.NO_URL_KEY
            if len(chan.url) > 0:
                group = chan.url
            elif not include_no_group:
                continue
            groups.setdefault(group, [])
            groups[group].append(i)
        return groups

    def to_m3u_plus_playlist(self) -> str:
        out = f"{self._build_header()}\n"
        for channel in self._channels:
            out += channel.to_m3u_plus_playlist_entry()
        return out

    def to_m3u8_playlist(self) -> str:
        out = f"{m3u.M3U_HEADER_TAG}\n"
        for channel in self._channels:
            out += channel.to_m3u8_playlist_entry()
        return out

    def copy(self) -> 'M3UPlaylist':
        new_pl = M3UPlaylist()
        for channel in self._channels:
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
        out = f"attributes: {self._attributes}\n" if len(self._attributes) > 0 else ''
        index = 0
        for chan in self._channels:
            out += f"{index}: {chan}\n"
            index += 1
        return out

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
    header = rows[0].strip()
    body = rows[1:]
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
    chunks = _chunk_body(body, cores)
    results: List[AsyncResult] = []
    log.debug("spawning a pool of processes (one per core) to parse the playlist")
    with mp.Pool(processes=cores) as pool:
        for chunk in chunks:
            begin = chunk["begin"]
            end = chunk["end"]
            log.debug(
                "assigning a \"populate\" task (begin: %s, end: %s) to a process in the pool",
                begin,
                end
            )
            result = pool.apply_async(_populate, (body, begin, end))
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


def _build_chunk(begin: int, end: int) -> Dict[str, int]:
    return {
        "begin": begin,
        "end": end
    }


def _find_chunk_end(sub_list: List[str]) -> int:
    offset = len(sub_list)
    for offset, row in enumerate(sub_list):
        if m3u.is_extinf_row(row):
            log.debug(
                "chunking at the following row (offset %s) as it's an #EXTINF row:\n%s",
                offset,
                row
            )
            break
        if offset > 0 and m3u.is_url_row(row) and m3u.is_url_row(sub_list[offset - 1]):
            log.debug(
                "chunking at the following row (offset %s) as it's a url row after another url row:\n%s",
                offset,
                row
            )
            break
    return offset


def _compute_chunk(rows: List, start: int, min_size: int) -> Dict[str, int]:
    length = len(rows)
    sub_list = rows[start + min_size:]
    if length - start > min_size:
        log.debug(
            "there are enough remaining rows (%s left) to populate at least one full-size chunk",
            length - start
        )
        offset = _find_chunk_end(sub_list)
        end = start + min_size + offset
        log.debug("chunk end found at row %s", end)
        return _build_chunk(start, end)
    log.debug(
        "there are less than (or exactly) %s rows (%s left), so the chunk end is the list end",
        min_size,
        length - start
    )
    return _build_chunk(start, length)


def _chunk_body(rows: List, chunk_count: int, enforce_min_size: bool = True) -> List:
    length = len(rows)
    chunk_size = math.floor(length / chunk_count)
    if enforce_min_size and chunk_size < __MIN_CHUNK_SIZE:
        log.debug(
            "no chunking as each of the %s chunks would be smaller than the configured minimum (%s < %s)",
            chunk_count,
            chunk_size,
            __MIN_CHUNK_SIZE
        )
        return [
            {
                "begin": 0,
                "end": length
            }
        ]
    chunk_list = []
    start = 0
    while start < length:
        chunk: Dict[str, int] = _compute_chunk(rows, start, chunk_size)
        chunk_list.append(chunk)
        start = chunk["end"]
    log.debug("chunk_list: %s", chunk_list)
    return chunk_list


def _populate(rows: List, begin: int = 0, end: int = -1) -> 'M3UPlaylist':
    p_list = M3UPlaylist()
    if end == -1:
        end = len(rows)
    log.debug("populating playlist with rows from %s to %s", begin, end)
    entry = []
    previous_row = rows[begin]
    if m3u.is_extinf_row(previous_row):
        entry.append(rows[begin])
        log.debug("chunk starting with an #EXTINF row")
    for row in rows[begin + 1: end]:
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
