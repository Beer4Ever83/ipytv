#!/usr/bin/env python
import sys

import click

from ipytv import playlist
from ipytv.exceptions import WrongTypeException


@click.command()
@click.argument('input_json_file', type=click.Path(exists=True))
def main(input_json_file: click.Path) -> None:
    with open(input_json_file.name, "r", encoding='utf-8') as in_json:
        json_content = in_json.read()
        try:
            pl = playlist.loadj(json_content)
        except WrongTypeException as e:
            click.echo("The JSON file is not a valid JSON playlist")
            click.echo("Error: {}".format(e))
            return
        click.echo(pl.to_m3u_plus_playlist())

if __name__ == '__main__':
    main()
