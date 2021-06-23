import multiprocessing as mp

import math
import requests
from requests import RequestException

from ipytv.channel import IPTVChannel, IPTVAttr
from ipytv.exceptions import MalformedPlaylistException, URLException, WrongTypeException


class M3UPlaylist:
    NO_GROUP_KEY = '_NO_GROUP_'
    NO_URL_KEY = '_NO_URL_'
    # The value of MIN_CHUNK_SIZE cannot be smaller than 2
    MIN_CHUNK_SIZE = 20

    def __init__(self):
        self.list = None
        self.reset()

    @staticmethod
    def chunk_array(array, chunks):
        length = len(array)
        chunk_size = math.floor(length/chunks) + 1
        if chunk_size < M3UPlaylist.MIN_CHUNK_SIZE:
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
        return chunk_list

    @staticmethod
    def populate(array, begin=0, end=-1):
        pl = M3UPlaylist()
        if end == -1:
            end = len(array)
        entry = []
        previous_row = array[begin]
        if previous_row.startswith("#EXTINF:"):
            entry.append(array[begin])
        for index in range(begin+1, end):
            row = array[index].strip()
            if row.startswith("#EXTINF:"):
                if previous_row.startswith("#EXTINF:"):
                    # we are in the case of two adjacent #EXTINF rows, so we add a url-less entry.
                    # This shouldn't be theoretically allowed, but I've seen it happening in some IPTV playlists
                    # where isolated #EXTINF rows are used as group separators.
                    pl.add_entry(entry)
                    entry = []
                entry.append(row)
            elif row.startswith('#'):
                # case of a row with an unsupported tag or a comment, so we do nothing
                pass
            else:
                # case of a plain url row (no matter if preceded by an #EXTINF row)
                entry.append(row)
                pl.add_entry(entry)
                entry = []
            previous_row = row
        return pl

    @staticmethod
    def loada(array):
        if not isinstance(array, list):
            raise WrongTypeException("Wrong type: array expected")
        first_row = array[0].strip()
        if not first_row.startswith("#EXTM3U"):
            raise MalformedPlaylistException("Missing or misplaced #EXTM3U row")
        cores = mp.cpu_count()
        chunks = M3UPlaylist.chunk_array(array, cores)
        results = []
        out_pl = M3UPlaylist()
        with mp.Pool(processes=cores) as pool:
            for chunk in chunks:
                begin = chunk["begin"]
                end = chunk["end"]
                result = pool.apply_async(M3UPlaylist.populate, (array, begin, end))
                results.append(result)
            pool.close()
            for result in results:
                pl = result.get()
                out_pl.concatenate(pl)
        return out_pl

    @staticmethod
    def loads(string):
        if isinstance(string, str):
            return M3UPlaylist.loada(string.split("\n"))
        else:
            raise WrongTypeException("Wrong type: string expected")

    @staticmethod
    def loadf(filename):
        with open(filename) as file:
            buffer = file.readlines()
            return M3UPlaylist.loada(buffer)

    @staticmethod
    def loadu(url):
        try:
            response = requests.get(url, timeout=10)
            if response.ok:
                return M3UPlaylist.loads(response.text)
            else:
                raise URLException(
                    "Failure while opening {}.\nResponse status code: {}".format(url, response.status_code)
                )
        except RequestException as exception:
            raise URLException("Failure while opening {}.\nError: {}".format(url, exception)) from exception

    def reset(self):
        self.list = []

    def add_entry(self, entry):
        channel = IPTVChannel.from_playlist_entry(entry)
        self.add_channel(channel)

    def add_channel(self, channel):
        self.list.append(channel)

    def group_by_attribute(self, attribute=IPTVAttr.GROUP_TITLE.value, include_no_group=True):
        groups = {}
        for i in range(len(self.list)):
            ch = self.list[i]
            group = self.NO_GROUP_KEY
            if attribute in ch.attributes and len(ch.attributes[attribute]) > 0:
                group = ch.attributes[attribute]
            elif not include_no_group:
                continue
            groups.setdefault(group, [])
            groups[group].append(i)
        return groups

    def group_by_url(self, include_no_group=True):
        groups = {}
        for i in range(len(self.list)):
            ch = self.list[i]
            group = self.NO_URL_KEY
            if len(ch.url) > 0:
                group = ch.url
            elif not include_no_group:
                continue
            groups.setdefault(group, [])
            groups[group].append(i)
        return groups

    def to_m3u_plus_playlist(self):
        header = "#EXTM3U"
        out = header
        entry_pattern = '\n#EXTINF:{}{},{}\n{}'
        for channel in self.list:
            attrs = ''
            for attr in channel.attributes:
                attrs += ' {}="{}"'.format(attr, channel.attributes[attr])
            out += entry_pattern.format(
                channel.duration,
                attrs,
                channel.name,
                channel.url
            )
        return out

    def to_m3u8_playlist(self):
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

    def concatenate(self, pl):
        self.list += pl.list

    def copy(self):
        newpl = M3UPlaylist()
        for channel in self.list:
            newpl.add_channel(channel.copy())
        return newpl

    def __eq__(self, other):
        if not isinstance(other, M3UPlaylist) or \
                len(other.list) != len(self.list):
            return False
        for i in range(len(self.list)):
            if not other.list[i].__eq__(self.list[i]):
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        out = ''
        index = 0
        for c in self.list:
            out += "{}: {}\n".format(index, c)
            index += 1
        return out
