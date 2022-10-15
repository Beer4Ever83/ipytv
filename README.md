# IPyTV

A python3 library to parse IPTV playlists in the M3U Plus format.

[![Downloads](https://pepy.tech/badge/m3u-ipytv)](https://pepy.tech/project/m3u-ipytv)
[![Downloads](https://pepy.tech/badge/m3u-ipytv/month)](https://pepy.tech/project/m3u-ipytv)
[![Downloads](https://pepy.tech/badge/m3u-ipytv/week)](https://pepy.tech/project/m3u-ipytv)

## M3U Plus and IPTV

The M3U Plus format is a _de facto_ standard for distributing IPTV playlists on
the Internet.

The terms _IPTV playlist_ and _M3U Plus playlist_ are generally used
interchangeably, but in this repository **M3U Plus** refers to the data format,
while **IPTV Playlist** refers to playlists in M3U Plus format.

M3U Plus stems from
the [`extended M3U8`](https://en.wikipedia.org/wiki/M3U#Extended_M3U)
format, of which it supports only 2 tags (`#EXTM3U` and `#EXTINF`).

The syntax of the `#EXTM3U` and `#EXTINF` tags has been modified to include
extra attributes (e.g., logo, group, language). Unfortunately this has broken
the backward compatibility with the original M3U8 standard (as explained in
detail [here](#format-considerations)).

This library has been created from scratch to parse and handle the M3U Plus
format only. It does not fully support regular M3U8 playlists (only basic
channel attributes are parsed).

### Supported tags

Only `#EXTM3U`, `#EXTINF` and plain url rows are supported (i.e. they are parsed
and their value is made available as properties of an `IPTVChannel` object).

All tags that are found between an `#EXTINF` row and its related url row are
added as `extras` to a channel, but without performing any parsing (i.e. they're
treated like plain strings).

In the example below, the `#EXTVLCOPT` row is not parsed, but copied _as-is_:

```text
#EXTINF:-1 tvg-id="" tvg-name="hello" tvg-country="IT" tvg-url="" group-title="Greetings",Hello!
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0 
https://my-website.com/hello
```

## Installation

This library requires Python 3 (and the related `pip` installer).

**PLEASE NOTE**: the library makes use of the `multiprocessing.Pool` class that
requires some care when working with the
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

Use the `playlist.loadf(file)` function:

```python
from ipytv import playlist

file = "~/Documents/my_playlist.m3u"
pl = playlist.loadf(file)
print(pl.length())
```

#### from a URL

Use the `playlist.loadu(url)` function:

```python
from ipytv import playlist

url = "https://iptv-org.github.io/iptv/categories/classic.m3u"
pl = playlist.loadu(url)
print(pl.length())
```

#### From a string

Use the `playlist.loads(string)` function:

```python
from ipytv import playlist

string = """#EXTM3U
#EXTINF:-1 tvg-id="Rai 1" tvg-name="Rai 1" group-title="RAI",Rai 1
http://myown.link:80/luke/210274/78482"""
pl = playlist.loads(string)
print(pl.length())
```

#### From a list

Use the `playlist.loadl(rows)` function:

```python
from ipytv import playlist

rows = [
    '#EXTM3U',
    '#EXTINF:-1 tvg-id="Rai 1" tvg-name="Rai 1" group-title="RAI",Rai 1',
    'http://myown.link:80/luke/210274/78482'
]
pl = playlist.loadl(rows)
print(pl.length())
```

### M3UPlaylist class

Every load function above returns an object of the `M3UPlaylist` class.

This class models the concept of a playlist (which is, basically, a list of
channels) and offers methods to interact with the playlist itself and with its
channels.

There are two main properties in a playlist, and they are:

1. Attributes
2. Channels

What these properties are and how they can be accessed is described in the next
paragraphs.

### Accessing the attributes of a playlist

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

In alternative, when the name of the property is known beforehand, its value can
be retrieved with:

```python
from ipytv import playlist

url = "https://iptv-org.github.io/iptv/categories/kids.m3u"
pl = playlist.loadu(url)
attributes = pl.get_attributes()
tvg_url = pl.get_attribute("x-tvg-url")
print(f"x-tvg-url: {tvg_url}")
```

The attributes can also be added, modified and removed by using the following
methods:

```python
from ipytv.playlist import M3UPlaylist

pl = M3UPlaylist()
attribute_name = 'tvg-shift'
# Add the 'tvg-shift' attribute and set it to 1
pl.add_attribute(attribute_name, "1")
# Update the 'tvg-shift' attribute to -2
pl.update_attribute(attribute_name, "-2")
# Completely remove the 'tvg-shift' attribute
value_before_deletion = pl.remove_attribute(attribute_name)
```

There is also a method that allows to add multiple attributes at once (instead
of single attributes) in the form of a dictionary:

```python
pl.add_attributes({})
```

### Accessing the channels of a playlist

The `M3UPlaylist` class is basically a list of channels with some commodity
functions. The channels in a playlist can be accessed by using one of the
following methods.

#### Individually

By using the `get_channel(index)` method:

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

By looping over the channels in an `M3UPlaylist` object:

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

The channels can also be added, modified and removed by using the following
methods:

```python
from ipytv.playlist import M3UPlaylist
from ipytv.channel import IPTVChannel

pl = M3UPlaylist()
channel = IPTVChannel()
# Add a channel to the end of the list (last index)
pl.append_channel(channel)
# Insert a channel in the specified position (all succeeding channels are
# shifted right by 1 position)
pl.insert_channel(0, channel)
new_channel = IPTVChannel()
# Replace the second channel of the playlist with a new channel
pl.update_channel(1, new_channel)
# Remove the channel at the specified position (all succeeding channels are
# shifted left by 1 position)
old_channel = pl.remove_channel(0)
```

There are also two methods that allow to add list of channels (instead of single
channels):

```python
pl.append_channels([])
pl.insert_channels([])
```

### Accessing the properties of a channel

The `get_channels()` method of an M3UPlaylist object returns a list of
`IPTVChannel` objects.

An `IPTVChannel` object has 3 basic properties (`url`, `name` and
`duration`) and two optional fields: `attributes` (a dictionary) and `extras`
(a list).

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
    },
    extras=['#EXTVLCOPT:http-user-agent=Lavf53.32.100']
)
print(channel.name)
print(channel.attributes[IPTVAttr.GROUP_TITLE.value])
print(channel.extras[0])
```

The `IPTVAttr` enum class contains attribute names that are commonly found in
IPTV Playlists.

### The `doctor` module

Internet-sourced IPTV playlists, often contain a number of format errors. This
module wants to address some common errors.

The module contains three classes, each with its own scope:

1. `M3UDoctor`
    - It contains methods to fix errors in m3u files (i.e. errors that would
      make it impossible to load an m3u file as a playlist).
2. `IPTVChannelDoctor`

    - It contains methods to fix errors in a channel (i.e. errors in the
      attributes of an #EXTINF row).

3. `M3UPlaylistDoctor`

    - It applies the fixes in `IPTVChannelDoctor` to all channels in the
      playlist.

All the classes above offer one public static method named `sanitize()` that is
in charge of applying all different fixes. It can be used as follows:

```python
from ipytv.doctor import M3UDoctor, M3UPlaylistDoctor
from ipytv import playlist

with open('my-broken-playlist.m3u', encoding='utf-8') as in_file:
    content = in_file.readlines()
    fixed_content = M3UDoctor.sanitize(content)
    pl = playlist.loadl(fixed_content)
    fixed_pl = M3UPlaylistDoctor.sanitize(pl)
    with open('my-fixed-playlist.m3u', 'w', encoding='utf-8') as out_file:
        content = fixed_pl.to_m3u_plus_playlist()
        out_file.write(content)
```

### Logging

IPyTV supports python's
standard [logging system](https://docs.python.org/3/library/logging.html).

To enable IPyTV's logging, add a logging configuration to your application:

```python
import logging
from ipytv import playlist

logging.basicConfig(level=logging.INFO)
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
