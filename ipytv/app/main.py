#!/usr/bin/env python3
import sys

from app.model.channel import IPTVAttr
from app.model.playlist import M3UPlaylist
from app.m3u_tools import M3UFileDoctor


def die():
    print("error")
    sys.exit(1)


def create_one_file_per_group(pl, outfile):
    groups = pl.group_by_attribute(IPTVAttr.TVG_COUNTRY.value)
    for group in groups:
        print("group: {}".format(group))
        group_outfile = "{}_{}".format(outfile, group.split()[0])
        newpl = M3UPlaylist()
        for channel_index in groups[group]:
            # print("channel_index: {}".format(channel_index))
            newpl.add_channel(pl.list[int(channel_index)])
        with open(group_outfile, "w") as outf:
            outf.write(newpl.to_m3u_plus_playlist())
            print("file {} created".format(group_outfile))


def create_m3u8_file(pl, outfile):
    m3u8_filename = outfile.replace(".m3u", ".m3u8")
    with open(m3u8_filename, "w") as outfile:
        outfile.write(pl.to_m3u8_playlist())
        print("file {} created".format(m3u8_filename))


def main():
    if len(sys.argv) < 3:
        die()
    infile = sys.argv[1]
    outfile = sys.argv[2]
    M3UFileDoctor.fix_split_quoted_string(infile, outfile)
    pl = M3UPlaylist.loadf(outfile)
    # create_one_file_per_group(pl, outfile)
    # create_m3u8_file(pl, outfile)


if __name__ == "__main__":
    main()
