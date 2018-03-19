from bs4 import BeautifulSoup
import requests
import urllib
import re
import unidecode # to remove accents
import codecs
import lyrics as minilyrics

error = "Error: Could not find lyrics."
proxy = urllib.request.getproxies()

def _minilyrics(artist, song):
    service_name = "Mini Lyrics"
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

    return(lyrics, url, service_name, timed)

def _wikia(artist, song):
    service_name = "Wikia"
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
    return(lyrics, url, service_name)

def _musixmatch(artist, song):
    service_name = "Musixmatch"
    url = ""
    try:
        searchurl = "https://www.musixmatch.com/search/%s-%s/tracks" % (artist.replace(' ', '-'), song.replace(' ', '-'))
        header = {"User-Agent":"curl/7.9.8 (i686-pc-linux-gnu) libcurl 7.9.8 (OpenSSL 0.9.6b) (ipv6 enabled)"}
        searchresults = requests.get(searchurl, headers=header, proxies=proxy)
        soup = BeautifulSoup(searchresults.text, 'html.parser')
        page = re.findall('"track_share_url":"([^"]*)', soup.text)
        url = codecs.decode(page[0], 'unicode-escape')
        lyricspage = requests.get(url, headers=header, proxies=proxy)
        soup = BeautifulSoup(lyricspage.text, 'html.parser')
        lyrics = soup.text.split('"body":"')[1].split('","language"')[0]
        lyrics = lyrics.replace("\\n", "\n")
        lyrics = lyrics.replace("\\", "")
        if lyrics.strip() == "":
            lyrics = error
    except Exception:
        lyrics = error
    return(lyrics, url, service_name)

def _songmeanings(artist, song):
    service_name = "Songmeanings"
    url = ""
    try:
        searchurl = "http://songmeanings.com/m/query/?q=%s %s" % (artist, song)
        searchresults = requests.get(searchurl, proxies=proxy)
        soup = BeautifulSoup(searchresults.text, 'html.parser')
        url = ""
        for link in soup.find_all('a', href=True):
            if "songmeanings.com/m/songs/view/" in link['href']:
                url = "https:" + link['href']
                break
            elif "/m/songs/view/" in link['href']:
                result = "http://songmeanings.com" + link['href']
                lyricspage = requests.get(result, proxies=proxy)
                soup = BeautifulSoup(lyricspage.text, 'html.parser')
                url = "http://songmeanings.com" + link['href'][2:]
                break
            else:
                pass
        templyrics = soup.find_all("li")[4]
        lyrics = templyrics.getText()
        lyrics = lyrics.split("(r,s)};})();")[1]
    except Exception:
        lyrics = error
    if lyrics == "We are currently missing these lyrics.":
        lyrics = error

    #lyrics = lyrics.encode('cp437', errors='replace').decode('utf-8', errors='replace')
    return(lyrics, url, service_name)

def _songlyrics(artist, song):
    service_name = "Songlyrics"
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
    if "We do not have" in lyrics:
        lyrics = error
    return(lyrics, url, service_name)


def _genius(artist, song):
    service_name = "Genius"
    url = ""
    try:
        url = "http://genius.com/%s-%s-lyrics" % (artist.replace(' ', '-'), song.replace(' ', '-'))
        lyricspage = requests.get(url, proxies=proxy)
        soup = BeautifulSoup(lyricspage.text, 'html.parser')
        lyrics = soup.find("div", {"class": "lyrics"}).get_text()
        if artist.lower().replace(" ", "") not in soup.text.lower().replace(" ", ""):
            lyrics = error
    except Exception:
        lyrics = error
    return(lyrics, url, service_name)

def _versuri(artist, song):
    service_name = "Versuri"
    url = ""
    try:
        searchurl = "http://www.versuri.ro/q/%s+%s/" % (artist.replace(" ", "+"), song.replace(" ", "+"))
        searchresults = requests.get(searchurl, proxies=proxy)
        soup = BeautifulSoup(searchresults.text, 'html.parser')
        for x in soup.findAll('a'):
            if "/versuri/" in x['href']:
                url = "http://www.versuri.ro" + x['href']
                break
            else:
                pass
        if url is "":
            lyrics = error
        else:
            lyricspage = requests.get(url, proxies=proxy)
            soup = BeautifulSoup(lyricspage.text, 'html.parser')
            content = soup.find_all('div',{'id':'pagecontent'})[0]
            lyrics = str(content)[str(content).find("</script><br/>") + 14:str(content).find("<br/><br/><center>")]
            lyrics = lyrics.replace("<br/>", "")
    except Exception:
        lyrics = error
    return(lyrics, url, service_name)

# tab/chord services

def _ultimateguitar(artist, song):
    artist = unidecode.unidecode(artist)
    song = unidecode.unidecode(song)
    url_pt1 = 'https://www.ultimate-guitar.com/search.php?view_state=advanced&band_name='
    url_pt2 = '&song_name='
    url_pt3 = '&type%5B%5D=300&type%5B%5D=200&rating%5B%5D=5&version_la='
    # song = song.replace('-', '+')
    # artist = artist.replace('-', '+')
    url = url_pt1+artist+url_pt2+song+url_pt3
    page = requests.get(url)

    soup = BeautifulSoup(page.content, 'html.parser')

    urls = []
    for a in soup.find_all(class_='song result-link js-search-spelling-link', href=True):
        urls.append(a['href'])

    return urls


def _cifraclub(artist, song):
    artist = unidecode.unidecode(artist)
    song = unidecode.unidecode(song)
    url = 'https://www.cifraclub.com.br/{}/{}'.format(artist.replace(" ", "-").lower(), song.replace(" ", "-").lower())

    return [url]

# don't even get to this point, but it's an option for source
# just got to change services_list3 list order
def _songsterr(artist, song):
    artist = unidecode.unidecode(artist)
    song = unidecode.unidecode(song)
    url = 'http://www.songsterr.com/a/wa/bestMatchForQueryString?s={}&a={}'.format(song, artist)
    return [url]
