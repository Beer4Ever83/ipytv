#!/usr/bin/env python

import click

from ipytv import playlist


@click.command()
@click.argument('input_json_file', type=click.Path(exists=False))

def main(input_json_file: str) -> None:
    with open(input_json_file, "r", encoding='UTF-8') as in_json:
        json_content = in_json.read()
        pl = playlist.loadj(json_content)
        click.echo(pl.to_m3u_plus_playlist())


if __name__ == "__main__":
    main()
