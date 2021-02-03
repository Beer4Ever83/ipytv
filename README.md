# IPyTV
A python library to handle IPTV playlists in m3u_plus format

## Details
The library distributes the loading job on multiples processes (usually one job
per logical core). To do so, it splits the file in chunks and assigns every
chunk to a worker process. 

# TO DO
## Improvements:
* Add annotations (e.g. type hints).
* Add code documentation.
* Add logging.
## Application:
* Implement a command-line application that makes use of the libraries for solving
real-life problems
    * Remove NSFW groups from an IPTV playlist.
    * Remove channels based on some criteria (e.g. channel name matching a
    pattern, the channel/entry duration).
    * Split the playlist into smaller playlists based on some criteria (per
    group, per title, etc.).
    * Sort the channels in a playlist according to some criteria.
    * Fix common errors in playlists (e.g. the ones in M3UDoctor).
    * Show duplicate channels.
* Open Points:
    * Should it offer the possibility of editing the playlist "in place" (if
    it's a file)?
## Service:
* Implement a service for fetching a transformed playlist.
    * Given a configuration file with a playlist (in the form of a URL or file),
    and some transformation rules, the service fetches/reads the original
    playlist, applies the requested transformation and offers the new playlist
    on its HTTP endpoint(s).
    * Open Points:
        * Do we have to implement a caching mechanism somehow? It could help in
        scenarios like when the URL is temporarily unreachable (in this case we
        serve the cached version).
        * Do we have to try to fetch the playlist from the URL regularly, apply
        the transformations and then serve the latest transformed version only?
        It may not be practical to implement an event-based fetch+transform
        sequence because the operation may take too long, and the request from
        the client may time-out while we're in the middle of the operation.
* Implement a service for transforming playlists on-the-fly.
    * A service that allows to upload a playlist (or a playlist url), to create
    transformation rules and to apply these rules to playlists on-the-fly. 
## Nice to have:
* Export playlist in other formats.

# License
This project is licensed under the terms of the MIT license.

See LICENSE.md for details.
