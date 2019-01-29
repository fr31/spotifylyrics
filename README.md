# Spotify Lyrics
[![Build Status](https://travis-ci.com/SimonIT/spotifylyrics.svg?branch=master)](https://travis-ci.com/SimonIT/spotifylyrics)
[![Current Release](https://img.shields.io/github/release/SimonIT/spotifylyrics.svg)](https://github.com/SimonIT/spotifylyrics/releases)
[![License](https://img.shields.io/github/license/SimonIT/spotifylyrics.svg)](https://github.com/SimonIT/spotifylyrics/blob/master/LICENSE)

Fetches and displays lyrics to currently playing song in the Spotify desktop client.

# how to
You can grab the latest release exe in the [release section](https://github.com/SimonIT/spotifylyrics/releases).

Just double click and start playing songs in spotify. 

If you get an error about api-ms-win-crt-runtime-l1-1-0.dll missing, you need this:

https://www.microsoft.com/en-us/download/details.aspx?id=48145

# running from source
If you want to run from source you need:

* Python 3.6.2 (probably any version of Python 3)
* pip install -r requirements.txt

Ubuntu/Debian Example:
```
sudo apt-get install python3-pip
git clone https://github.com/fr31/spotifylyrics.git
cd spotifylyrics/
sudo pip3 install -r requirements.txt
chmod +x SpotifyLyrics.pyw
./SpotifyLyrics.pyw
```

# screenshot
![example-img](https://i.imgur.com/2dUN17q.png)
