#!/usr/bin/env python

import click

from ipytv import doctor, playlist


@click.command()
@click.option('--no-sanitize', help='Skip sanitization of the playlist', is_flag=True)
@click.argument('input_m3u_file', type=click.Path(exists=True))

def main(input_m3u_file: str, no_sanitize: bool) -> None:
    sanitize = not no_sanitize
    with open(input_m3u_file, "r", encoding='UTF-8') as in_file:
        if sanitize:
            content = doctor.M3UDoctor.sanitize(in_file.readlines())
        else:
            content = in_file.readlines()
    try:
        pl = playlist.loadl(content)
    # pylint: disable=W0703
    # pylint: disable=W0133
    except Exception as e:
        click.echo("Exception while loading the specified M3U playlist")
        click.echo("Error: {}".format(e))
        click.Abort()
    if sanitize:
        pl = doctor.M3UPlaylistDoctor.sanitize(pl)
    json_pl = pl.to_json_playlist()
    click.echo(json_pl)

if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
