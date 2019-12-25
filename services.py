import codecs
import json
import os
import re
from urllib import request, parse

import pathvalidate
import requests
import unidecode  # to remove accents
from bs4 import BeautifulSoup

import lyrics as minilyrics

try:
    import spotify_lyric.crawlers.QQCrawler as QQCrawler
    import spotify_lyric.model_traditional_conversion.langconv as langconv
except ModuleNotFoundError:
    pass

ERROR = "Error: Could not find lyrics."
PROXY = request.getproxies()

if os.name == "nt":
    SETTINGS_DIR = os.getenv("APPDATA") + "\\SpotifyLyrics\\"
else:
    SETTINGS_DIR = os.path.expanduser("~") + "/.SpotifyLyrics/"
LYRICS_DIR = os.path.join(SETTINGS_DIR, "lyrics")


def _local(song):
    service_name = "Local"
    url = ""
    timed = False
    lyrics = ERROR

    if os.path.isdir(LYRICS_DIR):
        for file in os.listdir(LYRICS_DIR):
            file = os.path.join(LYRICS_DIR, file)
            if os.path.isfile(file):
                file_parts = os.path.splitext(file)
                file_extension = file_parts[1].lower()
                if file_extension in (".txt", ".lrc"):
                    file_name = file_parts[0].lower()
                    path_song_name = pathvalidate.sanitize_filename(song.name.lower())
                    path_artist_name = pathvalidate.sanitize_filename(song.artist.lower())
                    if path_song_name in file_name and path_artist_name in file_name:
                        with open(file, "r", encoding="UTF-8") as lyrics_file:
                            lyrics = lyrics_file.read()
                        timed = file_extension == ".lrc"
                        url = "file:///" + os.path.abspath(file)
                        break

    return lyrics, url, service_name, timed


def _minilyrics(song):
    service_name = "Mini Lyrics"
    url = ""
    timed = False
    try:
        data = minilyrics.MiniLyrics(song.artist, song.name)
        for item in data:
            if item['url'].endswith(".lrc"):
                url = item['url']
                break
        lyrics = requests.get(url, proxies=PROXY).text
        timed = True
    except Exception:
        lyrics = ERROR
    if url == "":
        lyrics = ERROR
    if song.artist.lower().replace(" ", "") not in lyrics.lower().replace(" ", ""):
        lyrics = ERROR
        timed = False

    return lyrics, url, service_name, timed


def _rentanadviser(song):
    service_name = "RentAnAdviser"
    url = ""

    possible_url = "https://www.rentanadviser.com/en/subtitles/getsubtitle.aspx?%s" % parse.urlencode({
        "artist": song.artist,
        "song": song.name,
        "type": "lrc",
    })
    possible_text = requests.get(possible_url, proxies=PROXY)
    soup = BeautifulSoup(possible_text.text, 'html.parser')
    text_container = soup.find(id="ctl00_ContentPlaceHolder1_lbllyrics")

    if text_container:
        url = possible_url
        text_container.h3.decompose()
        for br in text_container.find_all("br"):
            br.replace_with("\n")

        lyrics = text_container.get_text()
        timed = True
    else:
        lyrics = ERROR
        timed = False

    return lyrics, url, service_name, timed


def _qq(song):
    url = ""
    try:
        qq = QQCrawler.QQCrawler()
        sid = qq.getSongId(artist=song.artist, song=song.name)
        url = qq.getLyticURI(sid)
    except (AttributeError, NameError) as e:
        return ERROR, url, "QQ", False

    lrc_string = ""
    for line in requests.get(url, proxies=PROXY).text.splitlines():
        line_text = line.split(']')
        lrc_string += "]".join(line_text[:-1]) + langconv.Converter('zh-hant').convert(line_text)

    return lrc_string, url, qq.name, True


def _wikia(song):
    service_name = "Wikia"
    url = ""
    try:
        lyrics = minilyrics.LyricWikia(song.artist, song.name)
        url = "http://lyrics.wikia.com/%s:%s" % (song.artist.replace(' ', '_'), song.name.replace(' ', '_'))
    except Exception:
        lyrics = ERROR
    if "TrebleClef.png" in lyrics:
        lyrics = "(Instrumental)"
    if "Instrumental" in lyrics:
        lyrics = "(Instrumental)"
    if lyrics == "error":
        lyrics = ERROR
    return lyrics, url, service_name


def _musixmatch(song):
    service_name = "Musixmatch"
    url = ""
    try:
        search_url = "https://www.musixmatch.com/search/%s-%s/tracks" % (
            song.artist.replace(' ', '-'), song.name.replace(' ', '-'))
        header = {"User-Agent": "curl/7.9.8 (i686-pc-linux-gnu) libcurl 7.9.8 (OpenSSL 0.9.6b) (ipv6 enabled)"}
        search_results = requests.get(search_url, headers=header, proxies=PROXY)
        soup = BeautifulSoup(search_results.text, 'html.parser')
        page = re.findall('"track_share_url":"([^"]*)', soup.text)
        url = codecs.decode(page[0], 'unicode-escape')
        lyrics_page = requests.get(url, headers=header, proxies=PROXY)
        soup = BeautifulSoup(lyrics_page.text, 'html.parser')
        lyrics = soup.text.split('"body":"')[1].split('","language"')[0]
        lyrics = lyrics.replace("\\n", "\n")
        lyrics = lyrics.replace("\\", "")
        if lyrics.strip() == "":
            lyrics = ERROR
        album = soup.find(class_="mxm-track-footer__album")
        if album:
            song.album = album.find(class_="mui-cell__title").getText()
    except Exception:
        lyrics = ERROR
    return lyrics, url, service_name


def _songmeanings(song):
    service_name = "Songmeanings"
    url = ""
    try:
        search_url = "http://songmeanings.com/m/query/?q=%s %s" % (song.artist, song.name)
        search_results = requests.get(search_url, proxies=PROXY)
        soup = BeautifulSoup(search_results.text, 'html.parser')
        url = ""
        for link in soup.find_all('a', href=True):
            if "songmeanings.com/m/songs/view/" in link['href']:
                url = "https:" + link['href']
                break
            elif "/m/songs/view/" in link['href']:
                result = "http://songmeanings.com" + link['href']
                lyrics_page = requests.get(result, proxies=PROXY)
                soup = BeautifulSoup(lyrics_page.text, 'html.parser')
                url = "http://songmeanings.com" + link['href'][2:]
                break
            else:
                pass
        temp_lyrics = soup.find_all("li")[4]
        lyrics = temp_lyrics.getText()
        lyrics = lyrics.split("(r,s)};})();")[1]
    except Exception:
        lyrics = ERROR
    if lyrics == "We are currently missing these lyrics.":
        lyrics = ERROR

    # lyrics = lyrics.encode('cp437', errors='replace').decode('utf-8', errors='replace')
    return lyrics, url, service_name


def _songlyrics(song):
    service_name = "Songlyrics"
    url = ""
    try:
        artistm = song.artist.replace(" ", "-")
        songm = song.name.replace(" ", "-")
        url = "http://www.songlyrics.com/%s/%s-lyrics" % (artistm, songm)
        lyrics_page = requests.get(url, proxies=PROXY)
        soup = BeautifulSoup(lyrics_page.text, 'html.parser')
        lyrics = soup.find(id="songLyricsDiv").get_text()
    except Exception:
        lyrics = ERROR
    if "Sorry, we have no" in lyrics:
        lyrics = ERROR
    if "We do not have" in lyrics:
        lyrics = ERROR
    return lyrics, url, service_name


def _genius(song):
    service_name = "Genius"
    url = ""
    try:
        url = "http://genius.com/%s-%s-lyrics" % (song.artist.replace(' ', '-'), song.name.replace(' ', '-'))
        lyrics_page = requests.get(url, proxies=PROXY)
        soup = BeautifulSoup(lyrics_page.text, 'html.parser')
        lyrics = soup.find("div", {"class": "lyrics"}).get_text()
        if song.artist.lower().replace(" ", "") not in soup.text.lower().replace(" ", ""):
            lyrics = ERROR
    except Exception:
        lyrics = ERROR
    return lyrics, url, service_name


def _versuri(song):
    service_name = "Versuri"
    url = ""
    try:
        search_url = "https://www.versuri.ro/q/%s+%s/" % \
                     (song.artist.replace(" ", "+").lower(), song.name.replace(" ", "+").lower())
        search_results = requests.get(search_url, proxies=PROXY)
        soup = BeautifulSoup(search_results.text, 'html.parser')
        for search_results in soup.findAll('a'):
            if "/versuri/" in search_results['href']:
                link_text = search_results.getText().lower()
                if song.artist.lower() in link_text and song.name.lower() in link_text:
                    url = "https://www.versuri.ro" + search_results['href']
                    break
            else:
                pass
        if url == "":
            lyrics = ERROR
        else:
            lyrics_page = requests.get(url, proxies=PROXY)
            soup = BeautifulSoup(lyrics_page.text, 'html.parser')
            content = soup.find_all('div', {'id': 'pagecontent'})[0]
            lyrics = str(content)[str(content).find("</script><br/>") + 14:str(content).find("<br/><br/><center>")]
            lyrics = lyrics.replace("<br/>", "")
        if "nu există" in lyrics:
            lyrics = ERROR
    except Exception:
        lyrics = ERROR
    return lyrics, url, service_name


# tab/chord services

def _ultimateguitar(song):
    artist = unidecode.unidecode(song.artist)
    title = unidecode.unidecode(song.name)
    url_pt1 = 'https://www.ultimate-guitar.com/search.php?view_state=advanced&band_name='
    url_pt2 = '&song_name='
    url_pt3 = '&type%5B%5D=300&type%5B%5D=200&rating%5B%5D=5&version_la='
    # song = song.replace('-', '+')
    # artist = artist.replace('-', '+')
    url = url_pt1 + artist + url_pt2 + title + url_pt3
    page = requests.get(url)

    if page.status_code == 200:
        soup = BeautifulSoup(page.content, 'html.parser')

        search_results_element = soup.find_all('div', {'class': 'js-store'})[0]
        search_results_data = json.loads(search_results_element["data-content"])

        urls = []
        data = search_results_data["store"]["page"]["data"]
        if "results" in data.keys():
            for result in data["results"]:
                urls.append(result["tab_url"])

        return urls
    return []


def _cifraclub(song):
    artist = unidecode.unidecode(song.artist)
    title = unidecode.unidecode(song.name)
    url = 'https://www.cifraclub.com.br/{}/{}'.format(artist.replace(" ", "-").lower(), title.replace(" ", "-").lower())

    return [url]


# don't even get to this point, but it's an option for source
# just got to change services_list3 list order
def _songsterr(song):
    artist = unidecode.unidecode(song.artist)
    title = unidecode.unidecode(song.name)
    url = 'http://www.songsterr.com/a/wa/bestMatchForQueryString?s={}&a={}'.format(title, artist)
    return [url]


def _tanzmusikonline(song):
    try:
        token_request = requests.get('https://www.tanzmusik-online.de/search')
        search = BeautifulSoup(token_request.content, 'html.parser').find(id="page-wrapper")
        if search:
            token = ""
            for input_field in search.find("form").find_all("input"):
                if input_field.get("name") == "_token":
                    token = input_field.get("value")
                    break
            page = 1
            highest_page = 2
            song_urls = []
            base_result_url = 'https://www.tanzmusik-online.de/search/result'
            while page < highest_page:
                search_results = requests.post(base_result_url + "?page=" + str(page), proxies=PROXY,
                                               cookies=token_request.cookies,
                                               data={"artist": song.artist, "song": song.name, "_token": token,
                                                     "searchMode": "extended", "genre": 0, "submit": "Suchen"})
                search_soup = BeautifulSoup(search_results.content, 'html.parser')
                for song_result in search_soup.find_all(class_="song"):
                    song_urls.append(song_result.find(class_="songTitle").a.get("href"))
                if page == 1:
                    pagination = search_soup.find(class_="pagination")
                    if pagination:
                        for page_number_element in pagination.find_all("a"):
                            page_number = page_number_element.getText()
                            if page_number.isdigit():
                                highest_page = int(page_number) + 1
                page += 1

            language = requests.get("https://www.tanzmusik-online.de/locale/en", proxies=PROXY)
            for song_url in song_urls:
                page = requests.get(song_url, proxies=PROXY, cookies=language.cookies)

                soup = BeautifulSoup(page.content, 'html.parser')

                for dance in soup.find(class_="dances").find_all("div"):
                    dance_name = dance.a.getText().strip().replace("Disco Fox", "Discofox")
                    if dance_name not in song.dances:
                        song.dances.append(dance_name)

                details = soup.find(class_="songDetails")
                if details:
                    for detail in details.find_all(class_="line"):
                        classes = detail.i.get("class")
                        typ, text = detail.div.getText().split(":", 1)
                        if "fa-dot-circle-o" in classes:
                            if typ.strip().lower() == "album":
                                song.album = text.strip()
                        elif "fa-calendar-o" in classes:
                            song.year = int(text)
                        elif "fa-flag" in classes:
                            song.genre = text.strip()
                        elif "fa-music" in classes:
                            song.cycles_per_minute = int(text)
                        elif "fa-tachometer" in classes:
                            song.beats_per_minute = int(text)
    except requests.exceptions.ConnectionError as e:
        print(e)


def _welchertanz(song):
    try:
        interpreter_request = requests.get("https://www.welcher-tanz.de/interpreten/", proxies=PROXY)
        interpreter_soup = BeautifulSoup(interpreter_request.content, 'html.parser')
        interpreter_links = []
        for interpreter in interpreter_soup.find_all(class_="chip"):
            if song.artist.lower() in interpreter.getText().split("(", 1)[0].strip().lower():
                interpreter_links.append(interpreter.get("href"))
        for interpreter_link in interpreter_links:
            interpreter_songs = requests.get("https://www.welcher-tanz.de" + interpreter_link, proxies=PROXY)
            interpreter_songs_soup = BeautifulSoup(interpreter_songs.content, 'html.parser')
            for interpreter_song in interpreter_songs_soup.find(class_="card-content").find_all("tr"):
                infos = interpreter_song.find_all("td")
                if infos and song.name.lower() in infos[1].getText().strip().lower():
                    dances = infos[2].find_all("a")
                    for dance in dances:
                        dance_name = dance.getText().strip() \
                            .replace("Cha-Cha-Cha", "Cha Cha Cha") \
                            .replace("Wiener", "Viennese") \
                            .replace("Walzer", "Waltz") \
                            .replace("Foxtrott", "Foxtrot")
                        if dance_name != "---" and dance_name not in song.dances:
                            song.dances.append(dance_name)
    except requests.exceptions.ConnectionError as e:
        print(e)
