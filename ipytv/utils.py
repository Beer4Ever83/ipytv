"""Multiple utility functions for the ipytv package.

Functions:
    group_by_similarity: Create multiple playlists from a single playlist by grouping similar entries together.
"""
import re
from difflib import SequenceMatcher
from typing import List, Dict

from ipytv.channel import IPTVChannel, IPTVAttr
from ipytv.playlist import M3UPlaylist


# Regular expression patterns to match season and episode numbers.
# This should match "S05E10" or "s:01 e:13"
SEASON_AND_EPISODE_PATTERN_1 = re.compile(r'\s+(S[:=]?\d+)?\s*(E[:=]?\d+).*', re.IGNORECASE)
# This should match " 01x05" or " 05.13" but not " 1920x1024"
SEASON_AND_EPISODE_PATTERN_2 = re.compile(r'\s+(\d{1,2})[x.](\d+)(?:\s+|$).*', re.IGNORECASE)
# This should match "Something.2" but not "25.10.2024"
SEASON_AND_EPISODE_PATTERN_3 = re.compile(r'(?<![0-9])\.(\d+)$', re.IGNORECASE)


def extract_series(pl: M3UPlaylist, exclude_single=False) -> (List[M3UPlaylist], M3UPlaylist):
    """Create multiple playlists from a single playlist by grouping similar entries together.

    Args:
        pl: The playlist to group.
        exclude_single: When set to True, the function will remove from the result all the playlists with only a single
                        channel

    Returns:
        A list of playlists.
    """
    playlists: List[M3UPlaylist] = []
    not_series_playlist = M3UPlaylist()
    not_series_playlist.add_attributes(pl.get_attributes())
    for channel in pl:
        # If it doesn't look like a series, we skip it
        if not is_series(channel.name):
            not_series_playlist.append_channel(channel)
            continue
        # Find the playlist that is most similar to the current channel
        found = False
        for playlist in playlists:
            if is_good_fit(channel, playlist, use_group_title=True):
                playlist.append_channel(channel)
                found = True
                break
        # If no similar playlist was found, create a new playlist and add the channel to it
        if not found:
            new_pl = M3UPlaylist()
            new_pl.add_attributes(pl.get_attributes())
            new_pl.append_channel(channel)
            # We insert at the top, because it's more likely that the next channel belongs to the most recently added
            # playlist. In some cases, this will speed up the inner loop considerably. A quick test I made, for the same
            # playlist on the same machine, using playlists.append(new_pl) here causes the overall time to be 65
            # minutes. When playlists.insert(0, new_pl) is used, instead, it took less than 3 minutes. Of course the
            # performance improvement is strictly dependent on the order of the entries in your playlist, but the good
            # thing is that the worst case is the same for both approaches.
            playlists.insert(0, new_pl)

    new_playlists = []
    if exclude_single:
        for pl in playlists:
            if pl.length() > 1:
                new_playlists.append(pl)
        return new_playlists, not_series_playlist

    return playlists, not_series_playlist


def quick_extract_series(pl: M3UPlaylist, exclude_single=False) -> (List[M3UPlaylist], M3UPlaylist):
    """Create multiple playlists from a single playlist by grouping similar entries together.

    Args:
        pl: The playlist to group.
        exclude_single: When set to True, the function will remove from the result all the playlists with only a single
                        channel

    Returns:
        A list of playlists.
    """
    title_playlist_map: Dict[str: M3UPlaylist] = {}
    not_series_playlist = M3UPlaylist()
    not_series_playlist.add_attributes(pl.get_attributes())
    for channel in pl:
        # If it doesn't look like a series, we skip it
        if not is_series(channel.name):
            not_series_playlist.append_channel(channel)
            continue

        show_name = extract_show_name(channel.name).lower()
        if not show_name in title_playlist_map:
            title_playlist_map[show_name] = M3UPlaylist()
            title_playlist_map[show_name].add_attributes(pl.get_attributes())
        title_playlist_map[show_name].append_channel(channel)

    playlists: List[M3UPlaylist] = list(title_playlist_map.values())
    if exclude_single:
        playlists = [pl for pl in playlists if pl.length() > 1]

    return playlists, not_series_playlist


def is_good_fit(ch: IPTVChannel, pl: M3UPlaylist, exhaustive=False, use_group_title=False) -> bool:
    """Check if a channel belongs to a playlist. The channel belongs to the playlist if the similarity ratio is greater
    or equal than 0.95 (the comparison is done in a case-insensitive manner).

    Args:
        ch: The channel to check.
        pl: The playlist to check.
        exhaustive: If True, the function will check all the channels in the playlist. If False, the function will only
                    check the first channel.
        use_group_title:    If True, the comparison between the channel and the playlist is done also taking into
                            consideration the "group_title" attribute.

    Returns:
        True if the channel belongs to the playlist, False otherwise.
    """
    threshold = 0.95
    total = 0.0
    index = 0
    gt_attr = IPTVAttr.GROUP_TITLE.value
    candidate_group_title = ch.attributes.get(gt_attr) if gt_attr in ch.attributes else ""
    candidate_show_name = extract_show_name(ch.name.lower())
    for index, channel in enumerate(pl):
        playlist_show_name = extract_show_name(channel.name.lower())
        if candidate_show_name == playlist_show_name:
            total += 1
        else:
            if use_group_title:
                playlist_group_title = channel.attributes.get(gt_attr) if gt_attr in channel.attributes else ""
                total += SequenceMatcher(
                    a=f"{candidate_group_title}+{candidate_show_name}",
                    b=f"{playlist_group_title}+{playlist_show_name}"
                ).quick_ratio()
            else:
                total += SequenceMatcher(a=candidate_show_name, b=playlist_show_name).quick_ratio()
        if not exhaustive:
            break
    if total / (index+1) >= threshold:
        return True
    return False


def _calculate_similarity_score(a: str, b: str) -> float:
    if a == b:
        return 1.0
    return SequenceMatcher(a=a, b=b).quick_ratio()


def is_series(channel_name: str) -> bool:
    if re.search(SEASON_AND_EPISODE_PATTERN_1, channel_name) \
        or re.search(SEASON_AND_EPISODE_PATTERN_2, channel_name) \
        or re.search(SEASON_AND_EPISODE_PATTERN_3, channel_name):
        return True
    return False



def extract_show_name(channel_name: str) -> str:
    """Extract the show name from a channel name. In other words: it tries to detect the season and episode numbers and
    remove them (along with everything following these numbers, if any).

    Args:
        channel_name: The channel.

    Returns:
        The show name without season and episode numbers.
    """
    if re.search(SEASON_AND_EPISODE_PATTERN_1, channel_name):
        return SEASON_AND_EPISODE_PATTERN_1.sub("", channel_name)
    elif re.search(SEASON_AND_EPISODE_PATTERN_2, channel_name):
        return SEASON_AND_EPISODE_PATTERN_2.sub("", channel_name)
    elif re.search(SEASON_AND_EPISODE_PATTERN_3, channel_name):
        return SEASON_AND_EPISODE_PATTERN_3.sub("", channel_name)
    return channel_name

