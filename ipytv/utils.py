"""Multiple utility functions for the ipytv package.

Functions:
    group_by_similarity: Create multiple playlists from a single playlist by grouping similar entries together.
"""
from difflib import SequenceMatcher
from typing import List

from ipytv.channel import IPTVChannel
from ipytv.playlist import M3UPlaylist


def group_by_similarity(pl: M3UPlaylist) -> List[M3UPlaylist]:
    """Create multiple playlists from a single playlist by grouping similar entries together.

    Args:
        pl: The playlist to group.

    Returns:
        A list of playlists.
    """
    # Create a list of playlists
    playlists: List[M3UPlaylist] = []
    # Iterate over the channels in the playlist
    for channel in pl:
        # Get the channel name
        name = channel.name
        # Find the playlist that is most similar to the current channel
        found = False
        for playlist in playlists:
            if is_good_fit(channel, playlist):
                found = True
                break
        # If no similar playlist was found, create a new playlist
        if not found:
            new_pl = M3UPlaylist()
            new_pl.add_attributes(pl.get_attributes())
            new_pl.append_channel(channel)
            playlists.append(new_pl)
    return playlists

def is_good_fit(ch: IPTVChannel, pl: M3UPlaylist) -> bool:
    """Check if a channel belongs to a playlist.

    Args:
        ch: The channel to check.
        pl: The playlist to check.

    Returns:
        True if the channel belongs to the playlist, False otherwise.
    """
    threshold = 0.8
    total = 0
    for channel in pl:
        total += SequenceMatcher(None, ch.name, channel.name).ratio()
    if total / pl.length() >= threshold:
        return True
    return False