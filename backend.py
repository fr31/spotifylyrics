# -*- coding: utf-8 -*-
import requests
import urllib
import time
import os
import sys
import re
import webbrowser # to open link on browser
import services as s
import subprocess

if sys.platform == "win32":
    import win32process
    import psutil
    import win32gui
elif sys.platform == "linux":
    import dbus
else:
    pass

# With Sync. Of course, there is one for now, but for the sake of
# make the code a little bit more cleaner, is declared.
services_list1 = [s._minilyrics]

# Without Sync.
services_list2 = [s._wikia, s._musixmatch, s._songmeanings, s._songlyrics, s._genius, s._versuri]

services_list3 = [s._ultimateguitar, s._cifraclub, s._songsterr]

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
    global current_service

    if current_service == len(services_list2)-1: current_service = -1

    if sync == True:
        lyrics, url, service_name, timed = s._minilyrics(artist, song)
        current_service = -1

    if sync == True and not lyrics_found(lyrics) or sync == False:
        timed = False
        for i in range (current_service+1, len(services_list2)):
            lyrics, url, service_name = services_list2[i](artist, song)
            current_service = i
            if lyrics_found(lyrics):
                lyrics = lyrics.replace("&amp;", "&").replace("`", "'").strip()
                break

    #return "Error: Could not find lyrics."  if the for loop doens't find any lyrics
    return(lyrics, url, service_name, timed)


def lyrics_found(lyrics):
    error = "Error: Could not find lyrics."
    return lyrics != error


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
    
    # remove letters between parenthesis from song title
    song_name_without_parenthesis_content = re.sub(' \(.*?\)', '', song, flags=re.DOTALL)
    lyrics_content = load_lyrics(artist, song_name_without_parenthesis_content, sync)

    # if not found try without removing letters between parenthesis
    if not lyrics_found(lyrics_content[0]):
        song_name_with_parenthesis_content = re.sub('[\(\\.)]', '', song)
        lyrics_content = load_lyrics(artist, song_name_with_parenthesis_content, sync)
        
    return lyrics_content


def next_lyrics():
    global current_service
    lyrics, url, service_name, timed = load_lyrics(artist, song)
    return (lyrics, url, service_name, timed)

def load_chords():
    for i in range(len(services_list3)):
        urls = services_list3[i](artist, song)
        if len(urls) != 0: 
            webbrowser.open(urls[0])
            break

def getwindowtitle():
    if sys.platform == "win32":
        spotifypids = []
        for proc in psutil.process_iter():
            if proc.name() == 'Spotify.exe':
                spotifypids.append(proc.pid)

        def enum_window_callback(hwnd, pid):
            tid, current_pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == current_pid and win32gui.IsWindowVisible(hwnd):
                windows.append(hwnd)

        windows = []
        windowname = ''        

        try:
            for pid in spotifypids:
                win32gui.EnumWindows(enum_window_callback, pid)
                for item in windows:
                    if win32gui.GetWindowText(item) != '':
                        windowname = win32gui.GetWindowText(item)
                        raise StopIteration
        except StopIteration: pass

    elif sys.platform == "darwin":
        windowname = ''
        try:
            command = "osascript getCurrentSong.AppleScript"
            windowname = subprocess.check_output(["/bin/bash", "-c", command]).decode("utf-8")
        except Exception:
            pass
    else:
        windowname = ''
        try:
            session = dbus.SessionBus()
            spotifydbus = session.get_object("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
            spotifyinterface = dbus.Interface(spotifydbus, "org.freedesktop.DBus.Properties")
            metadata = spotifyinterface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
        except Exception:
            pass
        try:
            command = "xwininfo -tree -root"
            windows = subprocess.check_output(["/bin/bash", "-c", command]).decode("utf-8")
            spotify = ''
            for line in windows.splitlines():
                if '("spotify" "Spotify")' in line:
                    if " - " in line:
                        spotify = line
                        break
                spotify = 'Spotify Lyrics'
            if spotify == '':
                windowname = 'Spotify'
        except Exception:
            pass
        if windowname != 'Spotify' and windowname != 'Spotify Lyrics':
            try:
                windowname = "%s - %s" %(metadata['xesam:artist'][0], metadata['xesam:title'])
            except Exception:
                pass
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
        if float(version()) >= float(currentversion):
            return(True)
        else:
            return(False)
    except Exception:
        return(True)

def version():
    version = "1.21"
    return(version)

def open_spotify():
    if sys.platform == "win32":
        if getwindowtitle() == "":
            path = os.getenv("APPDATA") + '\Spotify\Spotify.exe'
            subprocess.Popen(path)
        else:
            pass
    elif sys.platform == "linux":
        if getwindowtitle() == "":
            subprocess.Popen("spotify")
        else:
            pass
    elif sys.platform == "darwin":
        # I don't have a mac so I don't know if this actually works
        # If it does, please let me know, if it doesn't please fix it :)
        if getwindowtitle() == "":
            subprocess.Popen("open -a Spotify")
        else:
            pass
    else:
        pass

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
