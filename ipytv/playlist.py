import logging
import math
import multiprocessing as mp
from typing import List, Dict

import requests
from requests import RequestException

from ipytv import m3u_tools
from ipytv.channel import IPTVChannel, IPTVAttr
from ipytv.exceptions import MalformedPlaylistException, URLException, WrongTypeException

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class M3UPlaylist:
    NO_GROUP_KEY = '_NO_GROUP_'
    NO_URL_KEY = '_NO_URL_'
    # The value of __MIN_CHUNK_SIZE cannot be smaller than 2
    __MIN_CHUNK_SIZE = 20

    def __init__(self):
        self.list = None
        self.attributes = None
        self.reset()

    @staticmethod
    def chunk_array(array: List, chunk_count: int) -> List:
        length = len(array)
        chunk_size = math.floor(length / chunk_count) + 1
        if chunk_size < M3UPlaylist.__MIN_CHUNK_SIZE:
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

    @staticmethod
    def populate(array: List, begin: int = 0, end: int = -1) -> 'M3UPlaylist':
        p_list = M3UPlaylist()
        if end == -1:
            end = len(array)
        log.debug("populating playlist with rows from %s to %s", begin, end)
        entry = []
        previous_row = array[begin]
        if m3u_tools.is_extinf_row(previous_row):
            entry.append(array[begin])
            log.debug("it seems that the previous chunk ended with an EXTINF row")
        for index in range(begin+1, end):
            row = array[index].strip()
            log.debug("parsing row: %s", row)
            if m3u_tools.is_extinf_row(row):
                if m3u_tools.is_extinf_row(previous_row):
                    # we are in the case of two adjacent #EXTINF rows; so we add a url-less entry.
                    # This shouldn't be theoretically allowed, but I've seen it happening in some
                    # IPTV playlists where isolated #EXTINF rows are used as group separators.
                    log.warning("adjacent #EXTINF rows detected")
                    p_list.add_entry(entry)
                    log.debug("adding entry to the playlist: %s", entry)
                    entry = []
                entry.append(row)
            elif m3u_tools.is_comment_or_tag_row(row):
                # case of a row with a non-supported tag or a comment; so we do nothing
                log.warning("commented row or unsupported tag found: %s", row)
            else:
                # case of a plain url row (regardless if preceded by an #EXTINF row or not)
                entry.append(row)
                log.debug("adding entry to the playlist: %s", entry)
                p_list.add_entry(entry)
                entry = []
            previous_row = row
        return p_list

    @staticmethod
    def loada(array: List) -> 'M3UPlaylist':
        if not isinstance(array, list):
            log.error("expected %s, got %s", type([]), type(array))
            raise WrongTypeException("Wrong type: array (List) expected")
        first_row = array[0].strip()
        if not m3u_tools.is_m3u_header_row(first_row):
            log.error(
                "the playlist's first row should start with \"#EXTM3U\", but it's \"%s\"",
                first_row
            )
            raise MalformedPlaylistException("Missing or misplaced #EXTM3U row")
        out_pl = M3UPlaylist()
        out_pl.parse_header(first_row)
        cores = mp.cpu_count()
        log.info("%s cores detected", cores)
        chunks = M3UPlaylist.chunk_array(array, cores)
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
                result = pool.apply_async(M3UPlaylist.populate, (array, begin, end))
                results.append(result)
            pool.close()
            log.debug("pool destroyed")
            for result in results:
                p_list = result.get()
                out_pl.concatenate(p_list)
        return out_pl

    @staticmethod
    def loads(string: str) -> 'M3UPlaylist':
        if isinstance(string, str):
            return M3UPlaylist.loada(string.split("\n"))
        log.error("expected %s, got %s", type(''), type(string))
        raise WrongTypeException("Wrong type: string expected")

    @staticmethod
    def loadf(filename: str) -> 'M3UPlaylist':
        if not isinstance(filename, str):
            log.error("expected %s, got %s", type(''), type(filename))
            raise WrongTypeException("Wrong type: string expected")
        with open(filename, encoding='utf-8') as file:
            buffer = file.readlines()
            return M3UPlaylist.loada(buffer)

    @staticmethod
    def loadu(url: str) -> 'M3UPlaylist':
        if not isinstance(url, str):
            log.error("expected %s, got %s", type(''), type(url))
            raise WrongTypeException("Wrong type: string expected")
        try:
            response = requests.get(url, timeout=10)
            if response.ok:
                return M3UPlaylist.loads(response.text)
            raise URLException(
                f"Failure while opening {url}.\nResponse status code: {response.status_code}"
            )
        except RequestException as exception:
            raise URLException(
                f"Failure while opening {url}.\nError: {exception}"
            ) from exception

    def parse_header(self, header: str) -> None:
        attrs = header.replace('#EXTM3U ', '')
        for attr in attrs.split():
            entry = attr.split("=")
            if len(entry) == 2:
                name = entry[0].replace('"', '')
                value = entry[1].replace('"', '')
                self.attributes[name] = value

    def build_header(self)-> str:
        out = "#EXTM3U"
        for attr in self.attributes:
            out += f' {attr}="{self.attributes[attr]}"'
        return out

    def reset(self) -> None:
        self.list = []
        self.attributes = {}
        log.debug("playlist reset")

    def add_entry(self, entry: List):
        channel = IPTVChannel.from_playlist_entry(entry)
        self.add_channel(channel)

    def add_channel(self, channel: IPTVChannel) -> None:
        self.list.append(channel)
        log.debug("channel added: %s", channel)

    def group_by_attribute(self, attribute: str = IPTVAttr.GROUP_TITLE.value,
                           include_no_group: bool = True) -> Dict:
        groups: Dict[str, List] = {}
        for i, chan in enumerate(self.list):
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
        for i, chan in enumerate(self.list):
            group = self.NO_URL_KEY
            if len(chan.url) > 0:
                group = chan.url
            elif not include_no_group:
                continue
            groups.setdefault(group, [])
            groups[group].append(i)
        return groups

    def to_m3u_plus_playlist(self) -> str:
        header = "#EXTM3U"
        out = header
        entry_pattern = '\n#EXTINF:{}{},{}\n{}'
        for channel in self.list:
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
        header = "#EXTM3U\n"
        out = header
        entry_pattern = "#EXTINF:{},{}\n{}\n"
        for channel in self.list:
            out += entry_pattern.format(
                channel.duration,
                channel.name,
                channel.url
            )
        return out

    def concatenate(self, p_list: 'M3UPlaylist') -> None:
        self.list += p_list.list

    def copy(self) -> 'M3UPlaylist':
        newpl = M3UPlaylist()
        for channel in self.list:
            newpl.add_channel(channel.copy())
        return newpl

    def __eq__(self, other: object) -> bool:
        length = len(self.list)
        if not isinstance(other, M3UPlaylist) or \
                len(other.list) != length:
            return False
        for i in range(length):
            if not other.list[i].__eq__(self.list[i]):
                return False
        return True

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __str__(self) -> str:
        out = ''
        index = 0
        for chan in self.list:
            out += f"{index}: {chan}\n"
            index += 1
        return out
