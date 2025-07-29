#!/usr/bin/env python
"""Command-line interface for converting M3U playlists to JSON format.

This module provides a CLI command that converts IPTV M3U playlist files
to JSON format, with optional sanitization of the playlist content.
"""

import click

from ipytv import doctor, playlist


@click.command()
@click.option('--no-sanitize', help='Skip sanitization of the playlist', is_flag=True)
@click.argument('input_m3u_file', type=click.Path(exists=True))
def iptv2json(input_m3u_file: str, no_sanitize: bool) -> None:
    """Convert M3U playlist to JSON format.

    Reads an M3U playlist file and converts it to JSON format. By default,
    the playlist content is sanitized to clean up common formatting issues.

    Args:
        input_m3u_file: Path to the input M3U playlist file
        no_sanitize: If True, skips sanitization of the playlist content

    Raises:
        click.Abort: If an error occurs during playlist loading or processing
    """
    sanitize = not no_sanitize
    with open(input_m3u_file, "r", encoding='UTF-8') as in_file:
        if sanitize:
            content = doctor.M3UDoctor.sanitize(in_file.readlines())
        else:
            content = in_file.readlines()
    try:
        pl = playlist.loadl(content)
        if sanitize:
            pl = doctor.M3UPlaylistDoctor.sanitize(pl)
        json_pl = pl.to_json_playlist()
        click.echo(json_pl)
    # pylint: disable=W0703
    # pylint: disable=W0133
    except Exception as e:
        click.echo("Exception while loading the specified M3U playlist")
        click.echo(f"Error: {e}")
        click.Abort()


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    iptv2json()
