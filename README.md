#Vine Compilation Bot#
This is a script written in Python (2.7) for scraping [Vine][1] data from the official [Vine API][2].  This project is comprised of two main scripts, the scraper and the renderer.  This currently does not work with Python 3.

The scraper uses [Pandas][3] (my favorite data analysis library) to process and sort the Vine response data, which also depends on [Numpy][6] to function.  Other dependencies are [requests][4] and [lxml][5] for scraping popular tags from the vine homepage.

The renderer employs [moviepy][7] to first composite each individual vine video with its title, user, rank, and optional channel/user image.  Moviepy uses ffmpeg to create the videos, which should be installed automatically now that moviepy uses [image.io][8] to handle that dependency.

##Scraping Abilities##
The main scraping options are official Vine channels (comedy, animals, urban, fashion, food etc.), user timelines, and tags.  

Playlists can be added using a combined source of tags and or users. For example, one could create a fight comp using the tags (fight, fights, vinefight, vinefights, fighting, knockedout, knockout).

The playlist file located in meta/playlists.csv contains three columns: name, tags, and users. Name specifies the playlist name, which will also be used as the filename for the playlist metadata. Tags are a space separated list of tags without the hashtag.  Users is a space separated list of userId numbers, not the username.

##Usage##

###Scraper###
Update all channels and playlists, retrieve all pages
> python scraper.py -u

Update all channels and playlists, retrieve <= n pages
> python scraper.py --update=15

Download vine video files for the top (90) vines in the specified vine  metadata file. Files are located in meta/ and are csv formatted.  The files are either for a channel, user, or playlist name.
> python scraper.py --download=comedy

Delete all temporary files, including metadata files. meta/playlists.csv is spared from this operation because it is not a temporary file.
> python scraper.py --flush

Delete just the rendered vines in render/
> python scraper.py --flush=render

###Renderer###
Render top n vines of the specified channel/playlist
> python render.py --name=comedy --limit=90

Individual vine renders can be found in render/ and final renders can be found in render/finals/ with the filename as the channel or playlist name

[1]: http://vine.co/
[2]: https://github.com/VineAPI/VineAPI/blob/master/endpoints.md
[3]: http://pandas.pydata.org/
[4]: http://docs.python-requests.org/en/latest/
[5]: http://lxml.de/
[6]: http://www.numpy.org/
[7]: https://github.com/Zulko/moviepy
[8]: http://imageio.github.io/