from PyLyrics import *
from bs4 import BeautifulSoup
import pywintypes
import win32gui
import requests
import time
import os

def getlyrics(songname):
    if songname.count(" - ") == 1:
        artist, song = songname.rsplit(" - ", 1)
    if songname.count(" - ") == 2:
        artist, song, garbage = songname.rsplit(" - ", 2)
    try:
        lyrics = PyLyrics.getLyrics(artist, song)
    except Exception:
        lyrics = "Error: Could not find lyrics."
    if lyrics == "Error: Could not find lyrics.":
        searchurl = "http://songmeanings.com/m/query/?q=%s %s" % (artist, song)
        try:
            searchresults = requests.get(searchurl)
            soup = BeautifulSoup(searchresults.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                if "songmeanings.com/m/songs/view/" in link['href']:
                    break
                elif "/m/songs/view/" in link['href']:
                    result = "http://songmeanings.com" + link['href']
                    lyricspage = requests.get(result)
                    soup = BeautifulSoup(lyricspage.text, 'html.parser')
                    break
                else:
                    pass
            templyrics = soup.find_all("li")[4]
            lyrics = templyrics.getText()
        except Exception:
            pass
    lyrics = lyrics.replace("&amp;", "&")
    lyrics = lyrics.replace("`", "'")
    return(lyrics)

def getwindowtitle():
    spotify = win32gui.FindWindow('SpotifyMainWindow', None)
    windowname = win32gui.GetWindowText(spotify)
    return(windowname)

def main():
    os.system("chcp 65001")
    os.system("cls")
    oldsongname = ""
    while True:
        songname = getwindowtitle()
        if oldsongname != songname:
            oldsongname = songname
            if songname != "Spotify":
                print(songname+"\n")
                lyrics = getlyrics(songname)
                print(lyrics+"\n")
        time.sleep(1)

if __name__ == '__main__':
    main()
