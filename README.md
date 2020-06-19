# Spotify Lyrics
[![Build Status](https://travis-ci.com/SimonIT/spotifylyrics.svg?branch=master)](https://travis-ci.com/SimonIT/spotifylyrics)
[![Current Release](https://img.shields.io/github/release/SimonIT/spotifylyrics.svg)](https://github.com/SimonIT/spotifylyrics/releases)
[![License](https://img.shields.io/github/license/SimonIT/spotifylyrics.svg)](https://github.com/SimonIT/spotifylyrics/blob/master/LICENSE)
[![GitHub All Releases](https://img.shields.io/github/downloads/SimonIT/spotifylyrics/total)](https://github.com/SimonIT/spotifylyrics/releases)

Fetches and displays lyrics to currently playing song in the Spotify desktop client.

# How to

You can grab the latest release in the [release section](https://github.com/SimonIT/spotifylyrics/releases).

## Windows

Download the .exe file.

Just double click and start playing songs in spotify.

It is possible that a warning of windows smartscreen appears. It's because the exe is unsigned (see [#22](https://github.com/SimonIT/spotifylyrics/issues/22)). You can allow the program to open by clicking on "More info" and "Run anyway".

If you get an error about api-ms-win-crt-runtime-l1-1-0.dll missing, you need this:

https://www.microsoft.com/en-us/download/details.aspx?id=48145

If the window opens and closes immidiatly, feel free to help fxing the problem in [#21](https://github.com/SimonIT/spotifylyrics/issues/21).

## Linux

Download the file without any file ending.

Make it executable via terminal with `chmod +x SpotifyLyrics` or via you file manager.

Now you can double click the executable and start playing songs in spotify.

## MacOS

Download the .app.zip file.

Extract the zip so you got a SpotifyLyrics.app directory.

Make a right click on the SpotifyLyrics.app. Click on open and and you can bypass the warning. The program should open and you can play your songs in spotify.

# Running from source
If you want to run from source you need:

* Python 3.6 (probably any version greater than Python 3.6)
* pip install -r requirements.txt

## Ubuntu/Debian example:
```
sudo apt install python3-pip
git clone https://github.com/SimonIT/spotifylyrics.git
cd spotifylyrics/
sudo pip3 install -r requirements.txt
chmod +x SpotifyLyrics.pyw
./SpotifyLyrics.pyw
```

# How to load lyrics from hard drive
You can store lyrics on you hard drive which can automatically loaded.

You have to put them on windows in `C:\Users\<User>\AppData\Roaming\SpotifyLyrics\lyrics` and on the other OS's in `/home/<User>/.SpotifyLyrics/lyrics`. Replace `<User>` with your username.
  
There you can put `.lrc` files with synced text (You can make them for example on [lrcgenerator.com](https://lrcgenerator.com/) or [www.megalobiz.com](https://www.megalobiz.com/lrc/maker)) or simple `.txt` files with non-synced text.
 
**Important: The file names must include the artist and the name of the song**

# Screenshot
![example-img](https://i.imgur.com/2dUN17q.png)
