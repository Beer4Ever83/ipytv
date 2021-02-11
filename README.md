# IPyTV
A python library to parse IPTV playlists in the M3U Plus format.


## Index (table of contents)
TO BE DONE


## M3U Plus and IPTV
The M3U Plus format is a _de facto_ standard for distributing IPTV playlists on
the Internet.

The terms _IPTV playlist_ and _M3U Plus playlist_ are generally used
interchangeably, but in this repository I will use **M3U Plus** when talking
about the format of the data, while I will prefer **IPTV Playlist** when talking
about playlists.

M3U Plus stems from the [`extended M3U8`](https://en.wikipedia.org/wiki/M3U#Extended_M3U)
format, of which it supports only 2 tags (`#EXTM3U` and `#EXTINF`).
 
The syntax of the `#EXTINF` tag has been extended for adding extra attributes
(e.g. logo, group, language). Unfortunately this broke the backward
compatibility with the original M3U8 standard (as explained in detail
[here](#format-considerations)).

This library has been created from scratch to parse and handle the M3U Plus
format only. Regular M3U8 playlists are not (currently?) supported.


## Usage
TO BE DONE

### Examples
TO BE DONE

## Format considerations
The extensions to the `#EXTINF` tag introduced by the M3U Plus format have
broken the compatibility with the M3U8 format.

This is what a standard `#EXTINF` row looks like:
```text
#EXTINF:-1,Rai 1
```
The [format](https://tools.ietf.org/html/rfc8216#section-4.3.2.1) is pretty
straightforward:
```text
#EXTINF:<duration>,[<title>]
```
Let's break it down:
1. the `#EXTINF:` tag
1. the duration of the content (as an integer or float, signed or not)
1. a comma character
1. a title

This is what an `#EXTINF` row in the M3U Plus format looks like:
```text
#EXTINF:-1 tvg-id="Rai 1" tvg-name="Rai 1" tvg-logo="https://static.epg.best/it/RaiUno.it.png" group-title="RAI",Rai 1
```
If we break it down, we see that points 3. and 4. have been added (and they
break the previous definition for the `#EXTINF` tag):
1. the `#EXTINF:` tag
1. the duration of the content (as an integer or float, signed or not)
1. a space
1. a variable-length, space-separated list of attributes 
1. a comma character
1. a title

The attributes in point 4 are in the `attribute="value"` format, where _value_
may also contain non-escaped commas (which really complicates the parsing
logic).

It's worth noting that the M3U8 RFC document specifies how
[attribute lists](https://tools.ietf.org/html/rfc8216#section-4.2) should be
formatted, but the M3U Plus implementation doesn't comply with the standard.

In conclusion, the M3U Plus format with its quirks and idiosyncrasies is hard to
read for humans and hard to parse for computers. It's an ugly format, but it's
too widespread to be ignored and for Python to lack a parsing library.

On a funny note, this is how the VLC programmers named the
[parsing function](https://github.com/videolan/vlc/blob/474c90392ede9916f068fcb3f860ba220d4c5b11/modules/demux/playlist/m3u.c#L398)
for the IPTV playlists in the M3U Plus format:
```c
static void parseEXTINFIptvDiots( char *psz_string,
                                  char *(*pf_dup)(const char *),
                                  struct entry_meta_s *meta )
```


## License
This project is licensed under the terms of the MIT license.

See [LICENSE.md](./LICENSE.md) for details.
