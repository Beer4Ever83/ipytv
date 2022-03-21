import logging
import math
import multiprocessing as mp
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
__MIN_CHUNK_SIZE = 20


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

    def build_header(self) -> str:
        out = M3U_HEADER_TAG
        for k, v in self._attributes.items():
            out += f' {k}="{v}"'
        return out

    def reset(self) -> None:
        self._channels = []
        self._attributes = {}
        self._iter_index = 0
        log.info("playlist reset")

    def append_entry(self, entry: List):
        channel = ipytv.channel.from_playlist_entry(entry)
        self.append_channel(channel)

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
        out = self.build_header()
        entry_pattern = '\n#EXTINF:{}{},{}\n{}'
        for channel in self._channels:
            attrs = ''
            for attr in channel.attributes:
                attrs += f' {attr}="{channel.attributes[attr]}"'
            out += entry_pattern.format(
                channel.duration,
                attrs,
                channel.name,
                channel.url
            )
        return out

    def to_m3u8_playlist(self) -> str:
        out = f"{M3U_HEADER_TAG}"
        entry_pattern = "\n#EXTINF:{},{}\n{}"
        for channel in self._channels:
            out += entry_pattern.format(
                channel.duration,
                channel.name,
                channel.url
            )
        return out

    def copy(self) -> 'M3UPlaylist':
        new_pl = M3UPlaylist()
        for channel in self._channels:
            new_pl.append_channel(channel.copy())
        for k, v in self._attributes.items():
            new_pl.add_attribute(k, v)
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


def loada(array: List) -> 'M3UPlaylist':
    if not isinstance(array, list):
        log.error("expected %s, got %s", type([]), type(array))
        raise WrongTypeException("Wrong type: array (List) expected")
    first_row = array[0].strip()
    if not m3u.is_m3u_header_row(first_row):
        log.error(
            "the playlist's first row should start with \"%s\", but it's \"%s\"",
            M3U_HEADER_TAG,
            first_row
        )
        raise MalformedPlaylistException(f"Missing or misplaced {M3U_HEADER_TAG} row")
    out_pl = M3UPlaylist()
    out_pl.add_attributes(_parse_header(first_row))
    cores = mp.cpu_count()
    log.info("%s cores detected", cores)
    chunks = _chunk_array(array, cores)
    results = []
    log.info("spawning a pool of processes (one per core) to parse the playlist")
    with mp.Pool(processes=cores) as pool:
        for chunk in chunks:
            begin = chunk["begin"]
            end = chunk["end"]
            log.info(
                "assigning a \"populate\" task (begin: %s, end: %s) to a process in the pool",
                begin,
                end
            )
            result = pool.apply_async(_populate, (array, begin, end))
            results.append(result)
        pool.close()
        log.debug("pool destroyed")
        for result in results:
            p_list = result.get()
            out_pl.append_channels(p_list.get_channels())
    return out_pl


def loads(string: str) -> 'M3UPlaylist':
    if isinstance(string, str):
        return loada(string.split("\n"))
    log.error("expected %s, got %s", type(''), type(string))
    raise WrongTypeException("Wrong type: string expected")


def loadf(filename: str) -> 'M3UPlaylist':
    if not isinstance(filename, str):
        log.error("expected %s, got %s", type(''), type(filename))
        raise WrongTypeException("Wrong type: string expected")
    with open(filename, encoding='utf-8') as file:
        buffer = file.readlines()
        return loada(buffer)


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
    attrs = header.replace(f'{M3U_HEADER_TAG} ', '')
    attributes = {}
    for attr in attrs.split():
        entry = attr.split("=")
        if len(entry) == 2:
            name = entry[0].replace('"', '')
            value = entry[1].replace('"', '')
            attributes[name] = value
    return attributes


def _chunk_array(array: List, chunk_count: int) -> List:
    length = len(array)
    chunk_size = math.floor(length / chunk_count) + 1
    if chunk_size < __MIN_CHUNK_SIZE:
        return [
            {
                "begin": 0,
                "end": length
            }
        ]
    chunk_list = []
    overlap = 0
    end = 1
    for i in range(0, length-chunk_size, chunk_size):
        begin = i-overlap
        end = begin + chunk_size
        entry = {
            "begin": begin,
            "end": end
        }
        chunk_list.append(entry)
        overlap += 1
    # The last chunk can be bigger
    entry = {
        "begin": end-1,
        "end": length
    }
    chunk_list.append(entry)
    log.debug("chunk_list: %s", chunk_list)
    return chunk_list


def _populate(array: List, begin: int = 0, end: int = -1) -> 'M3UPlaylist':
    p_list = M3UPlaylist()
    if end == -1:
        end = len(array)
    log.debug("populating playlist with rows from %s to %s", begin, end)
    entry = []
    previous_row = array[begin]
    if m3u.is_extinf_row(previous_row):
        entry.append(array[begin])
        log.debug("it seems that the previous chunk ended with an EXTINF row")
    for index in range(begin+1, end):
        row = array[index].strip()
        log.debug("parsing row: %s", row)
        if m3u.is_extinf_row(row):
            if m3u.is_extinf_row(previous_row):
                # we are in the case of two adjacent #EXTINF rows; so we add a url-less entry.
                # This shouldn't be theoretically allowed, but I've seen it happening in some
                # IPTV playlists where isolated #EXTINF rows are used as group separators.
                log.warning("adjacent #EXTINF rows detected")
                p_list.append_entry(entry)
                log.debug("adding entry to the playlist: %s", entry)
                entry = []
            entry.append(row)
        elif m3u.is_comment_or_tag_row(row):
            # case of a row with a non-supported tag or a comment; so we do nothing
            log.warning("commented row or unsupported tag found: %s", row)
        else:
            # case of a plain url row (regardless if preceded by an #EXTINF row or not)
            entry.append(row)
            log.debug("adding entry to the playlist: %s", entry)
            p_list.append_entry(entry)
            entry = []
        previous_row = row
    return p_list
