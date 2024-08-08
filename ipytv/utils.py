"""Multiple utility functions for the ipytv package.

Functions:
    extract_series: Create multiple playlists from a single playlist by grouping episodes from the same series together.
"""
import re
from typing import Dict, Tuple

from ipytv.playlist import M3UPlaylist

NO_SERIES_KEY = '_NO_SERIES_'

# Regular expression patterns to match season and episode numbers.
# This should match "S05E10" or "s:01 e:13"
SEASON_AND_EPISODE_PATTERN_1 = re.compile(r'\s+(S[:=]?\d+)?\s*(E[:=]?\d+).*', re.IGNORECASE)
# This should match " 01x05" or " 05.13" but not " 1920x1024"
SEASON_AND_EPISODE_PATTERN_2 = re.compile(r'\s+(\d{1,2})[x.](\d+)(?:\s+|$).*', re.IGNORECASE)
# This should match "Something.2" but not "25.10.2024"
SEASON_AND_EPISODE_PATTERN_3 = re.compile(r'(?<![0-9])\.(\d+)$', re.IGNORECASE)


def extract_series(playlist: M3UPlaylist, exclude_single=False) -> Tuple[Dict[str, M3UPlaylist], M3UPlaylist]:
    """Create multiple playlists from a single playlist by grouping episodes from the same series together.

    Args:
        playlist: The playlist to group.
        exclude_single: When set to True, the function will remove from the result all the playlists with only a single
                        channel (the assumption here is that a show with just one episode is not a series).

    Returns:
        A dictionary with show titles as keys and the related playlists as values, one for every series detected, plus
        an extra playlist with all the entries that don't look like series with the _NO_SERIES_ string as key.
    """
    title_playlist_map: Dict[str, M3UPlaylist] = {}
    not_series_playlist = M3UPlaylist()
    not_series_playlist.add_attributes(playlist.get_attributes())
    for channel in playlist:
        # If it doesn't look like a series, we skip it
        if not is_episode_from_series(channel.name):
            not_series_playlist.append_channel(channel)
            continue

        show_name = extract_show_name(channel.name).lower()
        if not show_name in title_playlist_map:
            title_playlist_map[show_name] = M3UPlaylist()
            title_playlist_map[show_name].add_attributes(playlist.get_attributes())
        title_playlist_map[show_name].append_channel(channel)

    if exclude_single:
        title_playlist_map = {k:v for k, v in title_playlist_map.items() if v.length() > 1}

    return title_playlist_map, not_series_playlist


def is_episode_from_series(channel_name: str) -> bool:
    """This function tells whether the name of a channel looks like an episode from a series.

    Args:
        channel_name:   The name from an IPTVChannel object (i.e. ch.name) to analyze.

    Returns:
        A boolean condition where True means that the channel looks like it's part of a series, False otherwise.
    """
    if re.search(SEASON_AND_EPISODE_PATTERN_1, channel_name) \
        or re.search(SEASON_AND_EPISODE_PATTERN_2, channel_name) \
        or re.search(SEASON_AND_EPISODE_PATTERN_3, channel_name):
        return True
    return False


def extract_show_name(channel_name: str) -> str:
    """Extract the show name from a channel name. In other words: it tries to detect the season and episode numbers and
    to remove them (along with everything following these numbers, if any).

    Args:
        channel_name: The channel.

    Returns:
        The show name without season and episode numbers.
    """
    if re.search(SEASON_AND_EPISODE_PATTERN_1, channel_name):
        return SEASON_AND_EPISODE_PATTERN_1.sub("", channel_name)
    if re.search(SEASON_AND_EPISODE_PATTERN_2, channel_name):
        return SEASON_AND_EPISODE_PATTERN_2.sub("", channel_name)
    if re.search(SEASON_AND_EPISODE_PATTERN_3, channel_name):
        return SEASON_AND_EPISODE_PATTERN_3.sub("", channel_name)
    return channel_name
