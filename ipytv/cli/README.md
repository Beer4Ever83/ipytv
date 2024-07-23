# iptv2json
A tool that makes use of the ipytv library to convert an m3u playlist into a json structure.
This allows the navigation of the playlist with standard tools like jq.

## Command
```shell
iptv2json [--no-sanitize] input.m3u
```

## Sample json output
```json
{
  "attributes": {
    "x-tvg-url": "http://myown.link:80/luke/220311/22311"
  },
  "channels": [
    {
      "name": "Rai 1",
      "duration": "-1",
      "url": "http://myown.link:80/luke/210274/78482",
      "attributes": {
        "tvg-id": "Rai 1",
        "tvg-name": "Rai 1",
        "tvg-logo": "https://static.epg.best/it/RaiUno.it.png",
        "group-title": "RAI"
      },
      "extras": [
        "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0"
      ]
    },
    {
      "name": "Rai 2",
      "duration": "-1",
      "url": "http://myown.link:80/luke/210274/78483",
      "attributes": {
        "tvg-id": "Rai 2",
        "tvg-name": "Rai 2",
        "tvg-logo": "https://static.epg.best/it/RaiDue.it.png",
        "group-title": "RAI"
      },
      "extras": []
    }
  ]
}
```

# json2iptv
A tool that makes use of the ipytv library to convert a json playlist (like the one produced by
`iptv2json`) into an m3u playlist.
The input json structure is validated against a schema and the conversion is rejected if the 
validation fails.
The output mp3 playlist is written to the standard output (it can be saved to a file by using
redirection).

## Command
```shell
json2iptv input.json
```

# Usage examples
For every channel in playlist.m3u, print only the channel name:
```shell
iptv2json playlist.m3u | jq '.channels[].name'
```

For every channel in playlist.m3u, print the channel name and the url:
```shell
iptv2json playlist.m3u | jq '.channels[] | {name: .name, url: .url}'
```

Print all the group titles in playlist.m3u in alphabetical order:
```shell
iptv2json playlist.m3u | jq '.channels[].attributes."group-title"' | sort -u
```

Take all the channels from playlist.m3u that don't have XXX in the group title and create a new 
sfw.m3u playlist:
```shell
iptv2json playlist.m3u | \
  jq 'del(.channels[] | select(.attributes."group-title" | contains("XXX")))' > sfw.json
json2iptv sfw.json > sfw.m3u
```
