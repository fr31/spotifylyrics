# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import urllib
import time
import os
import re
import lyrics as minilyrics

if os.name == "nt":
    import pywintypes
    import win32gui
else:
    import subprocess
    import dbus

def getlyrics(songname, sync=False):
    error = "Error: Could not find lyrics."
    artist = ""
    song = ""
    url = ""
    proxy = urllib.request.getproxies()
    if songname.count(" - ") == 1:
        artist, song = songname.rsplit(" - ", 1)
    if songname.count(" - ") == 2:
        artist, song, garbage = songname.rsplit(" - ", 2)
    if " / " in song:
        song, garbage = song.rsplit(" / ", 1)
    song = re.sub(' \(.*?\)', '', song, flags=re.DOTALL)

    def lyrics_minilyrics(artist, song):
        url = ""
        timed = False
        try:
            data = minilyrics.MiniLyrics(artist, song)
            for item in data:
                if item['url'].endswith(".lrc"):
                    url = item['url']
                    break
            lyrics = requests.get(url, proxies=proxy).text
            timed = True
        except Exception:
            lyrics = error
        if url == "":
            lyrics = error
        if artist.lower().replace(" ", "") not in lyrics.lower().replace(" ", ""):
            lyrics = error
            timed = False
        return(lyrics, url, timed)

    def lyrics_wikia(artist, song):
        url = ""
        try:
            lyrics = minilyrics.LyricWikia(artist, song)
            url = "http://lyrics.wikia.com/%s:%s" % (artist.replace(' ', '_'), song.replace(' ', '_'))
        except Exception:
            lyrics = error
        if "TrebleClef.png" in lyrics:
            lyrics = "(Instrumental)"
        if "Instrumental" in lyrics:
            lyrics = "(Instrumental)"
        if lyrics == "error":
            lyrics = error
        return(lyrics, url)

    def lyrics_musixmatch(artist, song):
        url = ""
        try:
            searchurl = "https://www.musixmatch.com/search/%s %s" % (artist, song)
            searchresults = requests.get(searchurl, proxies=proxy)
            soup = BeautifulSoup(searchresults.text, 'html.parser')
            page = re.findall('"track_share_url":"(http[s?]://www\.musixmatch\.com/lyrics/.+?)","', soup.text)
            url = page[0]
            lyricspage = requests.get(url, proxies=proxy)
            soup = BeautifulSoup(lyricspage.text, 'html.parser')
            lyrics = soup.text.split('"body":"')[1].split('","language"')[0]
            lyrics = lyrics.replace("\\n", "\n")
            lyrics = lyrics.replace("\\", "")
        except Exception:
            lyrics = error
        return(lyrics, url)

    def lyrics_songmeanings(artist, song):
        url = ""
        try:
            searchurl = "http://songmeanings.com/m/query/?q=%s %s" % (artist, song)
            searchresults = requests.get(searchurl, proxies=proxy)
            soup = BeautifulSoup(searchresults.text, 'html.parser')
            url = ""
            for link in soup.find_all('a', href=True):
                if "songmeanings.com/m/songs/view/" in link['href']:
                    url = link['href']
                    break
                elif "/m/songs/view/" in link['href']:
                    result = "http://songmeanings.com" + link['href']
                    lyricspage = requests.get(result, proxies=proxy)
                    soup = BeautifulSoup(lyricspage.text, 'html.parser')
                    url = link['href']
                    break
                else:
                    pass
            templyrics = soup.find_all("li")[4]
            lyrics = templyrics.getText()
        except Exception:
            lyrics = error
        if lyrics == "We are currently missing these lyrics.":
            lyrics = error
        return(lyrics, url)

    def lyrics_songlyrics(artist, song):
        url = ""
        try:
            artistm = artist.replace(" ", "-")
            songm = song.replace(" ", "-")
            url = "http://www.songlyrics.com/%s/%s-lyrics" % (artistm, songm)
            lyricspage = requests.get(url, proxies=proxy)
            soup = BeautifulSoup(lyricspage.text, 'html.parser')
            lyrics = soup.find(id="songLyricsDiv").get_text()
        except Exception:
            lyrics = error
        if "Sorry, we have no" in lyrics:
            lyrics = error
        return(lyrics, url)

    def lyrics_versuri(artist, song):
        url = ""
        try:
            try:
                searchurl = "https://searx.me/?q=site:versuri.ro/versuri/ %s %s&format=json" % (artist, song)
                searchresults = requests.get(searchurl, proxies=proxy).json()
                url = searchresults['results'][0]['url']
            except Exception:
                searchurl = "https://searx.space/?q=site:versuri.ro/versuri/ %s %s&format=json" % (artist, song)
                searchresults = requests.get(searchurl, proxies=proxy).json()
                url = searchresults['results'][0]['url']
            lyricspage = requests.get(url, proxies=proxy)
            soup = BeautifulSoup(lyricspage.text, 'html.parser')
            content = soup.find_all('div',{'id':'pagecontent'})[0]
            lyrics = str(content)[str(content).find("</script><br/>") + 14:str(content).find("<br/><br/><center>")]
            lyrics = lyrics.replace("<br/>", "")
        except Exception:
            lyrics = error
        return(lyrics, url)

    def lyrics_genius(artist, song):
        url = ""
        try:
            searchurl = "http://genius.com/search?q=%s %s" % (artist, song)
            searchresults = requests.get(searchurl, proxies=proxy)
            soup = BeautifulSoup(searchresults.text, 'html.parser')
            url = str(soup).split('song_link" href="')[1].split('" title=')[0]
            lyricspage = requests.get(url, proxies=proxy)
            soup = BeautifulSoup(lyricspage.text, 'html.parser')
            lyrics = soup.text.split('Lyrics\n\n\n')[1].split('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n              About')[0]
            lyrics = re.sub('googletag.*?}\);', '', lyrics, flags=re.DOTALL)
            if artist.lower().replace(" ", "") not in soup.text.lower().replace(" ", ""):
                lyrics = error
        except Exception:
            lyrics = error
        return(lyrics, url)

    if sync == True:
        lyrics, url, timed = lyrics_minilyrics(artist, song)
    else:
        lyrics = error
        timed = False
    if lyrics == error:
        lyrics, url = lyrics_wikia(artist, song)
    if lyrics == error:
        lyrics, url = lyrics_musixmatch(artist, song)
    if lyrics == error:
        lyrics, url = lyrics_songmeanings(artist, song)
    if lyrics == error:
        lyrics, url = lyrics_songlyrics(artist, song)
    if lyrics == error:
        lyrics, url = lyrics_genius(artist, song)
    if lyrics == error:
        lyrics, url = lyrics_versuri(artist, song)
    lyrics = lyrics.replace("&amp;", "&")
    lyrics = lyrics.replace("`", "'")
    lyrics = lyrics.strip()
    return(lyrics, url, timed)

def getwindowtitle():
    if os.name == "nt":
        spotify = win32gui.FindWindow('SpotifyMainWindow', None)
        windowname = win32gui.GetWindowText(spotify)
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
    version = 1.11
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
                lyrics, url, timed = getlyrics(songname)
                # print(lyrics+"\n")
        time.sleep(1)

if __name__ == '__main__':
    main()
