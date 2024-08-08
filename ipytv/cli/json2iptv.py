#!/usr/bin/env python

import click

from ipytv import playlist


@click.command()
@click.argument('input_json_file', type=click.Path(exists=True))
def main(input_json_file: str) -> None:
    with open(input_json_file, "r", encoding='utf-8') as in_json:
        json_content = in_json.read()
        try:
            pl = playlist.loadjstr(json_content)
        # pylint: disable=W0703
        except Exception as e:
            click.echo("Exception while loading the specified JSON playlist")
            click.echo("Error: {}".format(e))
            click.Abort()
        click.echo(pl.to_m3u_plus_playlist())

if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
