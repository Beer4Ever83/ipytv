"""Multiple utility functions for the ipytv package.

This module provides utility functions for processing IPTV playlists,
specifically for extracting and organizing TV series episodes from
larger playlists by detecting common episode naming patterns.

Constants:
    NO_SERIES_KEY: Constant for channels that don't belong to any series
    SEASON_AND_EPISODE_PATTERN_1: Regex for "S05E10" or "s:01 e:13" patterns
    SEASON_AND_EPISODE_PATTERN_2: Regex for "01x05" or "05.13" patterns
    SEASON_AND_EPISODE_PATTERN_3: Regex for "Something.2" patterns

Functions:
    extract_series: Create multiple playlists by grouping series episodes
    is_episode_from_series: Check if a channel name looks like a series episode
    extract_show_name: Extract show name by removing episode information
"""
import re
from typing import Dict, Tuple, Optional

from ipytv.playlist import M3UPlaylist

NO_SERIES_KEY = '_NO_SERIES_'

# Pre-compiled regular expression patterns to match season and episode numbers.
# This should match "S05E10" or "s:01 e:13"
_SEASON_AND_EPISODE_PATTERN_1 = re.compile(r'\s+(S[:=]?\d+)?\s*(E[:=]?\d+).*', re.IGNORECASE)
# This should match " 01x05" or " 05.13" but not " 1920x1024"
_SEASON_AND_EPISODE_PATTERN_2 = re.compile(r'\s+(\d{1,2})[x.](\d+)(?:\s+|$).*', re.IGNORECASE)
# This should match "Something.2" but not "25.10.2024"
_SEASON_AND_EPISODE_PATTERN_3 = re.compile(r'(?<![0-9])\.(\d+)$', re.IGNORECASE)


def _find_episode_pattern(channel_name: str) -> Optional[re.Pattern]:
    """Find which episode pattern matches the channel name.

    Args:
        channel_name: The channel name to check.

    Returns:
        The matching compiled pattern, or None if no pattern matches.
    """
    if _SEASON_AND_EPISODE_PATTERN_1.search(channel_name):
        return _SEASON_AND_EPISODE_PATTERN_1
    if _SEASON_AND_EPISODE_PATTERN_2.search(channel_name):
        return _SEASON_AND_EPISODE_PATTERN_2
    if _SEASON_AND_EPISODE_PATTERN_3.search(channel_name):
        return _SEASON_AND_EPISODE_PATTERN_3
    return None


def extract_series(playlist: M3UPlaylist, exclude_single: bool = False) -> Tuple[Dict[str, M3UPlaylist], M3UPlaylist]:
    """Create multiple playlists from a single playlist by grouping episodes from the same series together.

    Analyzes channel names to detect TV series episodes using common naming patterns,
    then groups episodes from the same series into separate playlists. Useful for
    organizing large IPTV playlists containing mixed content.

    Args:
        playlist: The M3UPlaylist to analyze and group by series.
        exclude_single: When True, removes playlists containing only one episode
                       (assumes single episodes are not series).

    Returns:
        A tuple containing:
        - Dictionary mapping show titles (lowercase) to M3UPlaylist objects,
          one for each detected series
        - M3UPlaylist containing all channels that don't match series patterns

    Example:
        >>> playlist = M3UPlaylist()
        >>> # ... add channels like "Breaking Bad S01E01", "Breaking Bad S01E02" ...
        >>> series_dict, non_series = extract_series(playlist)
        >>> series_dict["breaking bad"].length()
        12
        >>> non_series.length()  # channels that don't look like series
        5
    """
    title_playlist_map: Dict[str, M3UPlaylist] = {}
    not_series_playlist = M3UPlaylist()
    not_series_playlist.add_attributes(playlist.get_attributes())

    for channel in playlist:
        # If it doesn't look like a series, add to non-series playlist
        if not is_episode_from_series(channel.name):
            not_series_playlist.append_channel(channel)
            continue

        show_name = extract_show_name(channel.name).lower()
        if show_name not in title_playlist_map:
            title_playlist_map[show_name] = M3UPlaylist()
            title_playlist_map[show_name].add_attributes(playlist.get_attributes())
        title_playlist_map[show_name].append_channel(channel)

    if exclude_single:
        title_playlist_map = {k: v for k, v in title_playlist_map.items() if v.length() > 1}

    return title_playlist_map, not_series_playlist


def is_episode_from_series(channel_name: str) -> bool:
    """Check whether a channel name looks like an episode from a TV series.

    Uses multiple regex patterns to detect common episode naming conventions
    including season/episode numbers, episode numbering, and sequel patterns.

    Args:
        channel_name: The name from an IPTVChannel object to analyze.

    Returns:
        True if the channel name matches series episode patterns, False otherwise.

    Example:
        >>> is_episode_from_series("Breaking Bad S01E01")
        True
        >>> is_episode_from_series("Game of Thrones 1x05")
        True
        >>> is_episode_from_series("Movie.2")
        True
        >>> is_episode_from_series("News Channel")
        False
        >>> is_episode_from_series("Video 1920x1080")  # Resolution, not episode
        False
    """
    return _find_episode_pattern(channel_name) is not None


def extract_show_name(channel_name: str) -> str:
    """Extract the show name from a channel name by removing episode information.

    Detects season/episode numbers and removes them along with any trailing content
    to isolate the core show title. This enables grouping of episodes from the
    same series.

    Args:
        channel_name: The full channel name containing show title and episode info.

    Returns:
        The show name with episode information removed and trimmed.

    Example:
        >>> extract_show_name("Breaking Bad S01E01 Pilot")
        'Breaking Bad'
        >>> extract_show_name("Game of Thrones 1x05 The Wolf and the Lion")
        'Game of Thrones'
        >>> extract_show_name("The Matrix.2")
        'The Matrix'
        >>> extract_show_name("Regular Movie")  # No episode pattern
        'Regular Movie'
    """
    pattern = _find_episode_pattern(channel_name)
    if pattern:
        return pattern.sub("", channel_name).strip()
    return channel_name.strip()


if __name__ == "__main__":
    pass
