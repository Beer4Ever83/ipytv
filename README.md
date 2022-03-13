# IPyTV
A python3 library to parse IPTV playlists in the M3U Plus format.


## M3U Plus and IPTV
The M3U Plus format is a _de facto_ standard for distributing IPTV playlists on
the Internet.

The terms _IPTV playlist_ and _M3U Plus playlist_ are generally used
interchangeably, but in this repository **M3U Plus** refers to the data format,
while **IPTV Playlist** refers to playlists in M3U Plus format.

M3U Plus stems from the [`extended M3U8`](https://en.wikipedia.org/wiki/M3U#Extended_M3U)
format, of which it supports only 2 tags (`#EXTM3U` and `#EXTINF`).
 
The syntax of the `#EXTM3U` and `#EXTINF` tags has been modified to include
extra attributes (e.g., logo, group, language). Unfortunately this has broken
the backward compatibility with the original M3U8 standard (as explained in
detail [here](#format-considerations)).

This library has been created from scratch to parse and handle the M3U Plus
format only. It does not fully support regular M3U8 playlists.

## Installation
This library requires Python 3 (and the related `pip` installer).

**PLEASE NOTE**: the library makes use of the `multiprocessing.Pool` class 
that requires some care when working with the
[IDLE](https://docs.python.org/3/library/idle.html) environment.

To install the library system-wide, run:
```shell
pip install m3u-ipytv
```
To install it within a virtual environment, run:
```shell
python -m venv .venv
source .venv/bin/activate
pip install m3u-ipytv
```

## Usage

### Modules
The library comprises several modules, each with a specific area of competence:
- **channel**
  - Everything related to the handling of channels in a playlist.
- **doctor**
  - A collection of functions to fix common errors found in M3U files.
- **exceptions**
  - All the exceptions thrown by the library.
- **m3u**
  - Constants and functions related to M3U files.
- **playlist**
  - Everything related to the loading and handling of M3U playlists.


### Loading an IPTV Playlist

#### From a file
```python
from ipytv import playlist
file = "~/Documents/my_playlist.m3u"
pl = playlist.loadf(file)
print(pl.length())
```

#### from a URL
```python
from ipytv import playlist
url = "https://iptv-org.github.io/iptv/categories/classic.m3u"
pl = playlist.loadu(url)
print(pl.length())
```

#### From a string
```python
from ipytv import playlist
string = """#EXTM3U
#EXTINF:-1 tvg-id="Rai 1" tvg-name="Rai 1" group-title="RAI",Rai 1
http://myown.link:80/luke/210274/78482"""
pl = playlist.loads(string)
```

#### From an array (i.e. a list)
```python
from ipytv import playlist
array = [
    '#EXTM3U',
     '#EXTINF:-1 tvg-id="Rai 1" tvg-name="Rai 1" group-title="RAI",Rai 1',
     'http://myown.link:80/luke/210274/78482'
]
pl = playlist.loada(array)
```

### Accessing the global properties of a playlist
Key-value pairs that are specified in the `#EXTM3U` row are treated as
playlist-wide attributes (i.e. they apply to the playlist itself or to every
channel in the playlist).

For example the `x-tvg-url` part below:
```text
#EXTM3U x-tvg-url="http://myown.link:80/luke/220311/22311"
```

These attributes, in the form of a dictionary, can be accessed via the
`get_attributes()` method:
```python
from ipytv import playlist
url = "https://iptv-org.github.io/iptv/categories/kids.m3u"
pl = playlist.loadu(url)
attributes = pl.get_attributes()
for k, v in attributes.items():
    print(f'"{k}": "{v}"')
```

### Accessing the channels in the playlist

#### Individually
The channels in a playlist can be accessed individually by using the
`get_channel(index)` method:
```python
from ipytv import playlist
url = "https://iptv-org.github.io/iptv/categories/classic.m3u"
pl = playlist.loadu(url)
# Let's retrieve the first channel in the list
channel = pl.get_channel(0)
print(f'channel \"{channel.name}\": {channel.url}')
# The next line will throw IndexOutOfBoundsException
channel = pl.get_channel(-1)
```

#### Iteratively
You can also iterate over the channels in an `M3UPlaylist` object:
```python
from ipytv import playlist
url = "https://iptv-org.github.io/iptv/categories/classic.m3u"
pl = playlist.loadu(url)
for channel in pl:
    print(f'channel \"{channel.name}\": {channel.url}')
```

#### Low level
In all cases where the previous two access methods are not sufficient, the inner
channel list can be accessed via the `get_channels()` method:

```python
from ipytv import playlist

url = "https://iptv-org.github.io/iptv/categories/classic.m3u"
pl = playlist.loadu(url)
chan_list = pl.get_channels()
ten_channels = chan_list[:10] 
```

### Accessing the properties of a channel
The `get_channels()` method of an M3UPlaylist object returns a list of
`IPTVChannel` objects.

An `IPTVChannel` object has 3 basic properties (`url`, `name` and
`duration`) and an optional `attributes` dictionary.

For example:

```python
from ipytv.channel import IPTVAttr, IPTVChannel
channel = IPTVChannel(
    url="http://myown.link:80/luke/210274/78482",
    name="Rai 1",
    duration="-1",
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
The `IPTVAttr` enum class contains tags that are commonly found in IPTV
Playlists.

## Logging
IPyTV supports python's standard [logging system](https://docs.python.org/3/library/logging.html).

To enable IPyTV's logging, add a logging configuration to your application:
```python
import logging
from ipytv import playlist
logging.basicConfig(level=logging.DEBUG)
pl = playlist.loadu("https://iptv-org.github.io/iptv/categories/classic.m3u")
```

## Format considerations
The extensions to the `#EXTM3U` and `#EXTINF` tags introduced by the M3U Plus
format have broken the compatibility with the M3U8 format.

This is what a standard `#EXTINF` row should look like:
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
may also contain non-escaped commas (and this really complicates the parsing
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
static void parseEXTINFIptvDiots(...)
```
Just saying... :sweat_smile:

## License
This project is licensed under the terms of the MIT license.

See [LICENSE.txt](./LICENSE.txt) for details.
