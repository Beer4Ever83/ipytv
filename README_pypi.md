# IPyTV

**IPyTV** is a Python 3 library for parsing and handling IPTV playlists in the M3U Plus format.
It also provides two command-line utilities (`iptv2json` and `json2iptv`) for handling IPTV
playlists from the command line (for example using the `jq` tool).

## Features

- Parse M3U Plus playlists and access channel attributes.
- Search channels using regular expressions.
- Fix common errors in IPTV playlists with the `doctor` module.
- Serialize playlists to M3U Plus, M3U8, or JSON formats.
- Utilities for working with series and episodes in playlists.

## Installation

Install the library and the command-line tools using `pip`:

```shell
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install m3u-ipytv
```

## Repository

You can find the source code and the documentation in the
[GitHub repository](https://github.com/Beer4Ever83/ipytv)

The documentation for the `iptv2json` and `json2iptv` tools can be found
[here](https://github.com/Beer4Ever83/ipytv/tree/main/ipytv/cli)