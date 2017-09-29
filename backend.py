# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import urllib
import time
import os
import sys
import re
import lyrics as minilyrics
import services as s

if sys.platform == "win32":
    import win32gui
elif sys.platform == "darwin":
    import subprocess
else:
    import subprocess
    import dbus

# With Sync. Of course, there is one for now, but for the sake of
# make the code a little bit more cleaner, is declared.
services_list1 = [s._minilyrics]

# Without Sync.
services_list2 = [s._wikia, s._musixmatch, s._songmeanings, s._songlyrics, s._genius, s._versuri]

artist = ""
song = ""
url = ""

'''
current_service is used to store the current index of the list.
Useful to change the lyrics with the button "Next Lyric" if
the service returned a wrong song
'''
current_service = -1


def load_lyrics(artist, song, sync=False):
    error = "Error: Could not find lyrics."
    global current_service

    if current_service == len(services_list2)-1: current_service = -1

    if sync == True:
        lyrics, url, service_name, timed = s._minilyrics(artist, song)
        current_service = -1

    if sync == True and lyrics == error or sync == False:
        timed = False
        for i in range (current_service+1, len(services_list2)):
            lyrics, url, service_name = services_list2[i](artist, song)
            current_service = i
            if lyrics != error:
                lyrics = lyrics.replace("&amp;", "&").replace("`", "'").strip()
                break

    #return "Error: Could not find lyrics."  if the for loop doens't find any lyrics
    return(lyrics, url, service_name, timed)


def getlyrics(songname, sync=False):
    global artist, song, url, current_service
    artist = ""
    song = ""
    url = ""
    current_service = -1

    if songname.count(" - ") == 1:
        artist, song = songname.rsplit(" - ", 1)
    if songname.count(" - ") == 2:
        artist, song, garbage = songname.rsplit(" - ", 2)
    if " / " in song:
        song, garbage = song.rsplit(" / ", 1)
    song = re.sub(' \(.*?\)', '', song, flags=re.DOTALL)

    return load_lyrics(artist, song, sync)


def next_lyrics():
    global current_service
    lyrics, url, service_name, timed = load_lyrics(artist, song)
    return (lyrics, url, service_name, timed)




def getwindowtitle():
    if sys.platform == "win32":
        spotify = win32gui.FindWindow('SpotifyMainWindow', None)
        windowname = win32gui.GetWindowText(spotify)
    elif sys.platform == "darwin":
        windowname = ''
        try:
            command = "osascript getCurrentSong.AppleScript"
            windowname = subprocess.check_output(["/bin/bash", "-c", command]).decode("utf-8")
        except Exception:
            pass
    else:
        windowname = ''
        session = dbus.SessionBus()
        spotifydbus = session.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
        spotifyinterface = dbus.Interface(spotifydbus, "org.freedesktop.DBus.Properties")
        metadata = spotifyinterface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
        try:
            command = "xwininfo -tree -root"
            windows = subprocess.check_output(["/bin/bash", "-c", command]).decode("utf-8")
            spotify = ''
            for line in windows.splitlines():
                if '("spotify" "Spotify")' in line:
                    if " - " in line:
                        spotify = line
                        break
            if spotify == '':
                windowname = 'Spotify'
        except Exception:
            pass
        if windowname != 'Spotify':
            windowname = "%s - %s" %(metadata['xesam:artist'][0], metadata['xesam:title'])
    if "—" in windowname:
        windowname = windowname.replace("—", "-")
    if "Spotify - " in windowname:
        windowname = windowname.strip("Spotify - ")
    return(windowname)

def versioncheck():
    proxy = urllib.request.getproxies()
    try:
        currentversion = requests.get("https://raw.githubusercontent.com/fr31/spotifylyrics/master/currentversion", timeout=5, proxies=proxy).text
    except Exception:
        return(True)
    try:
        if version() >= float(currentversion):
            return(True)
        else:
            return(False)
    except Exception:
        return(True)

def version():
    version = 1.15
    return(version)

def main():
    if os.name == "nt":
        os.system("chcp 65001")
    def clear():
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
    clear()
    oldsongname = ""
    while True:
        songname = getwindowtitle()
        if oldsongname != songname:
            if songname != "Spotify":
                oldsongname = songname
                clear()
                # print(songname+"\n")
                lyrics, url, service_name, timed = getlyrics(songname)
                # print(lyrics+"\n")
        time.sleep(1)

if __name__ == '__main__':
    main()
