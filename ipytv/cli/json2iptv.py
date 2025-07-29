#!/usr/bin/env python
"""Command-line interface for converting JSON playlists to M3U format.

This module provides a CLI command that converts IPTV JSON playlist files
to M3U format for use with media players and IPTV applications.
"""

import click

from ipytv import playlist


@click.command()
@click.argument('input_json_file', type=click.Path(exists=True))
def json2iptv(input_json_file: str) -> None:
    """Convert JSON playlist to M3U format.

    Reads a JSON playlist file and converts it to M3U Plus format.
    The output is written to stdout and can be redirected to a file.

    Args:
        input_json_file: Path to the input JSON playlist file

    Raises:
        click.Abort: If an error occurs during playlist loading or processing
    """
    with open(input_json_file, "r", encoding='utf-8') as in_json:
        json_content = in_json.read()
        try:
            pl = playlist.loadjstr(json_content)
        # pylint: disable=W0703
        # pylint: disable=W0133
        except Exception as e:
            click.echo("Exception while loading the specified JSON playlist")
            click.echo(f"Error: {e}")
            click.Abort()
        click.echo(pl.to_m3u_plus_playlist())


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    json2iptv()
