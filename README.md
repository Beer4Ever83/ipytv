# IPyTV
A python library to parse IPTV playlists in the M3U Plus format.


## Index (table of contents)
TO BE DONE


## M3U Plus and IPTV
The M3U Plus format is a _de facto_ standard for distributing IPTV playlists on
the Internet.

The terms _IPTV playlist_ and _M3U Plus playlist_ are generally used
interchangeably, but in this repository **M3U Plus** refers to the data format,
while **IPTV Playlist** refers to playlists in M3U Plus format.

M3U Plus stems from the [`extended M3U8`](https://en.wikipedia.org/wiki/M3U#Extended_M3U)
format, of which it supports only 2 tags (`#EXTM3U` and `#EXTINF`).
 
The syntax of the `#EXTINF` tag has been extended for adding extra attributes
(e.g., logo, group, language). Unfortunately this has broken the backward
compatibility with the original M3U8 standard (as explained in detail
[here](#format-considerations)).

This library has been created from scratch to parse and handle the M3U Plus
format only. It does not fully support regular M3U8 playlists.

## Usage

### Load an IPTV Playlist from a file
```python
import ipytv
file = "~/Documents/my_playlist.m3u"
pl = ipytv.playlist.M3UPlaylist.loadf(file)
print(len(pl.list))
```

### Load an IPTV Playlist from a URL
```python
import ipytv
url = "https://iptv-org.github.io/iptv/categories/classic.m3u"
pl = ipytv.playlist.M3UPlaylist.loadu(url)
print(len(pl.list))
```

### Other loading methods
M3U Playlists can be loaded as a string as well as an array with the following
methods respectively:
```
ipytv.playlist.M3UPlaylist.loads(string)
ipytv.playlist.M3UPlaylist.loada(array)
```

### Access the channels in the playlist
Once loaded, the channels in a playlist can be accessed by using the
`list` property:
```python
import ipytv
url = "https://iptv-org.github.io/iptv/categories/classic.m3u"
pl = ipytv.playlist.M3UPlaylist.loadu(url)
firstChannel = pl.list[0]
```

### Access the properties of a channel
The `list` property of an M3UPlaylist object contains a list of `IPTVChannel`
objects.

An `IPTVChannel` object has 3 basic properties (`url`, `name` and
`duration`) and an optional `attributes` field.

The `attributes` property is a dictionary in the format:
```
{
    "attribute_1_name": "attribute_1_value",
    "attribute_2_name": "attribute_2_value",
    ...
    "attribute_N_name": "attribute_N_value"
}
```
For example:

```python
from ipytv.channel import IPTVAttr, IPTVChannel

channel = IPTVChannel(
    url="http://myown.link:80/luke/210274/78482",
    name="Rai 1",
    duration=-1,
    attributes={
        IPTVAttr.TVG_ID.value: "Rai 1",
        IPTVAttr.TVG_NAME.value: "Rai 1",
        IPTVAttr.TVG_LOGO.value: "https://static.epg.best/it/RaiUno.it.png",
        IPTVAttr.GROUP_TITLE.value: "RAI"
    }
)
print(channel.name)
print(channel.attributes[IPTVAttr.GROUP_TITLE.value])
```
The `IPTVAttr` enum class contains tags that are commonly found in IPT
Playlists.

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

See [LICENSE.txt](./LICENSE.txt) for details.
