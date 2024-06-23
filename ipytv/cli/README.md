# iptv2json
A tool that makes use of the ipytv file to convert an m3u playlist into a json structure.
This allows the navigation of the playlist with standard tools like jq.

## Command
```shell
iptv2json [--no-sanitize] input.m3u
```

## Json output
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
    }
  ]
}
```
