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
        path_song_name = pathvalidate.sanitize_filename(song.name.lower())
        path_artist_name = pathvalidate.sanitize_filename(song.artist.lower())
        for file in os.listdir(LYRICS_DIR):
            file = os.path.join(LYRICS_DIR, file)
            if os.path.isfile(file):
                file_parts = os.path.splitext(file)
                file_extension = file_parts[1].lower()
                if file_extension in (".txt", ".lrc"):
                    file_name = file_parts[0].lower()
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
    except Exception as error:
        print("%s: %s" % (service_name, error))
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

    search_url = "https://www.rentanadviser.com/en/subtitles/subtitles4songs.aspx?%s" % parse.urlencode({
        "src": song.artist + " " + song.name
    })
    try:
        search_results = requests.get(search_url, proxies=PROXY)
        soup = BeautifulSoup(search_results.text, 'html.parser')
        result_links = soup.find(id="tablecontainer").find_all("a")

        for result_link in result_links:
            if result_link["href"] != "subtitles4songs.aspx":
                lower_title = result_link.get_text().lower()
                if song.artist.lower() in lower_title and song.name.lower() in lower_title:
                    url = "https://www.rentanadviser.com/en/subtitles/%s&type=lrc" % result_link["href"]
                    break

        if url:
            possible_text = requests.get(url, proxies=PROXY)
            soup = BeautifulSoup(possible_text.text, 'html.parser')

            event_validation = soup.find(id="__EVENTVALIDATION")["value"]
            view_state = soup.find(id="__VIEWSTATE")["value"]

            lrc = requests.post(url, {"__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnlyrics",
                                      "__EVENTVALIDATION": event_validation,
                                      "__VIEWSTATE": view_state}, proxies=PROXY).text

            return lrc, url, service_name, True

    except Exception as error:
        print("%s: %s" % (service_name, error))
    return ERROR, url, service_name, False


def _megalobiz(song):
    service_name = "Megalobiz"
    url = ""

    search_url = "https://www.megalobiz.com/search/all?%s" % parse.urlencode({
        "qry": song.artist + " " + song.name,
        "display": "more"
    })
    try:
        search_results = requests.get(search_url, proxies=PROXY)
        soup = BeautifulSoup(search_results.text, 'html.parser')
        result_links = soup.find(id="list_entity_container").find_all("a", class_="entity_name")

        for result_link in result_links:
            lower_title = result_link.get_text().lower()
            if song.artist.lower() in lower_title and song.name.lower() in lower_title:
                url = "https://www.megalobiz.com%s" % result_link["href"]
                break

        if url:
            possible_text = requests.get(url, proxies=PROXY)
            soup = BeautifulSoup(possible_text.text, 'html.parser')

            lrc = soup.find("div", class_="lyrics_details").span.get_text()

            return lrc, url, service_name, True
    except Exception as error:
        print("%s: %s" % (service_name, error))
    return ERROR, url, service_name, False


def _qq(song):
    url = ""
    try:
        qq = QQCrawler.QQCrawler()
        sid = qq.getSongId(artist=song.artist, song=song.name)
        url = qq.getLyticURI(sid)
    except Exception as error:
        print("%s: %s" % ("QQ", error))
        return ERROR, url, "QQ", False

    lrc_string = ""
    for line in requests.get(url, proxies=PROXY).text.splitlines():
        line_text = line.split(']')
        lrc_string += "]".join(line_text[:-1]) + langconv.Converter('zh-hant').convert(line_text)

    return lrc_string, url, qq.name, True


def _wikia(song):
    service_name = "Wikia"
    url = ""
    timed = False
    try:
        lyrics, url, timed = minilyrics.LyricWikia(song.artist, song.name)
    except Exception as error:
        print("%s: %s" % (service_name, error))
        lyrics = ERROR
    if "TrebleClef.png" in lyrics:
        lyrics = "(Instrumental)"
    if "Instrumental" in lyrics:
        lyrics = "(Instrumental)"
    if lyrics == "error":
        lyrics = ERROR
    return lyrics, url, service_name, timed


def _syair(song):
    service_name = "Syair"
    url = ""

    search_url = "https://syair.info/search?%s" % parse.urlencode({
        "q": song.artist + " " + song.name
    })
    try:
        search_results = requests.get(search_url, proxies=PROXY)
        soup = BeautifulSoup(search_results.text, 'html.parser')

        result_container = soup.find("article", class_="sub")

        if result_container:
            result_list = result_container.find("div", class_="ul")

            if result_list:
                for result_link in result_list.find_all("a"):
                    name = result_link.get_text().lower()
                    if song.artist.lower() in name and song.name.lower() in name:
                        url = "https://syair.info%s" % result_link["href"]
                        break

                if url:
                    lyrics_page = requests.get(url, proxies=PROXY)
                    soup = BeautifulSoup(lyrics_page.text, 'html.parser')
                    lrc_link = ""
                    for download_link in soup.find_all("a"):
                        if "download.php" in download_link["href"]:
                            lrc_link = download_link["href"]
                            break
                    if lrc_link:
                        lrc = requests.get("https://syair.info%s" % lrc_link, proxies=PROXY,
                                           cookies=lyrics_page.cookies).text

                        return lrc, url, service_name, True
    except Exception as error:
        print("%s: %s" % (service_name, error))
    return ERROR, url, service_name, False


def _musixmatch(song):
    service_name = "Musixmatch"
    url = ""
    lyrics = ERROR
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
        if '"body":"' in soup.text:
            lyrics = soup.text.split('"body":"')[1].split('","language"')[0]
            lyrics = lyrics.replace("\\n", "\n")
            lyrics = lyrics.replace("\\", "")
            if lyrics.strip() == "":
                lyrics = ERROR
            album = soup.find(class_="mxm-track-footer__album")
            if album:
                song.album = album.find(class_="mui-cell__title").getText()
    except Exception as error:
        print("%s: %s" % (service_name, error))
    return lyrics, url, service_name


def _songmeanings(song):
    service_name = "Songmeanings"
    url = ""
    lyrics = ERROR
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
        lis = soup.find_all("li")
        if len(lis) > 4:
            temp_lyrics = lis[4]
            lyrics = temp_lyrics.getText()
            lyrics = lyrics.split("(r,s)};})();")[1]
    except Exception as error:
        print("%s: %s" % (service_name, error))
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
        url = "https://www.songlyrics.com/%s/%s-lyrics" % (artistm, songm)
        lyrics_page = requests.get(url, proxies=PROXY)
        soup = BeautifulSoup(lyrics_page.text, 'html.parser')
        lyrics = soup.find(id="songLyricsDiv").get_text()
        if "Sorry, we have no" in lyrics or "We do not have" in lyrics:
            lyrics = ERROR
        else:
            for info in soup.find("div", class_="pagetitle").find_all("p"):
                if "Album:" in info.get_text():
                    song.album = info.find("a").get_text()
    except Exception as error:
        print("%s: %s" % (service_name, error))
        lyrics = ERROR
    return lyrics, url, service_name


def _genius(song):
    service_name = "Genius"
    url = ""
    lyrics = ERROR
    try:
        url = "http://genius.com/%s-%s-lyrics" % (song.artist.replace(' ', '-'), song.name.replace(' ', '-'))
        lyrics_page = requests.get(url, proxies=PROXY)
        soup = BeautifulSoup(lyrics_page.text, 'html.parser')
        lyrics_container = soup.find("div", {"class": "lyrics"})
        if lyrics_container:
            lyrics = lyrics_container.get_text()
            if song.artist.lower().replace(" ", "") not in soup.text.lower().replace(" ", ""):
                lyrics = ERROR
    except Exception as error:
        print("%s: %s" % (service_name, error))
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
        if not url:
            lyrics = ERROR
        else:
            lyrics_page = requests.get(url, proxies=PROXY)
            soup = BeautifulSoup(lyrics_page.text, 'html.parser')
            content = soup.find_all('div', {'id': 'pagecontent'})[0]
            lyrics = str(content)[str(content).find("</script><br/>") + 14:str(content).find("<br/><br/><center>")]
            lyrics = lyrics.replace("<br/>", "")
        if "nu există" in lyrics:
            lyrics = ERROR
    except Exception as error:
        print("%s: %s" % (service_name, error))
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

    result = requests.get(url, proxies=PROXY)

    if result.status_code == 200:
        return [result.url]
    else:
        return []


# don't even get to this point, but it's an option for source
# just got to change services_list3 list order
def _songsterr(song):
    artist = unidecode.unidecode(song.artist)
    title = unidecode.unidecode(song.name)
    url = 'http://www.songsterr.com/a/wa/bestMatchForQueryString?s={}&a={}'.format(title, artist)
    return [url]


def _tanzmusikonline(song):
    try:
        token_request = requests.get('https://www.tanzmusik-online.de/search', timeout=30)
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
                                                     "searchMode": "extended", "genre": 0, "submit": "Suchen"},
                                               timeout=30)
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

            language = requests.get("https://www.tanzmusik-online.de/locale/en", proxies=PROXY, timeout=30)
            for song_url in song_urls:
                page = requests.get(song_url, proxies=PROXY, cookies=language.cookies, timeout=30)

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
    except Exception as error:
        print("%s: %s" % ("Tanzmusik Online", error))


def _welchertanz(song):
    try:
        interpreter_request = requests.get("https://tanzschule-woelbing.de/charts/interpreten/", proxies=PROXY)
        interpreter_soup = BeautifulSoup(interpreter_request.content, 'html.parser')
        interpreter_links = []
        for interpreter in interpreter_soup.find_all("a", class_="btn-dfeault"):
            if "/charts/interpreten/?artist-hash=" in interpreter.get("href") \
                    and song.artist.lower() in interpreter.getText().lower():
                interpreter_links.append(interpreter.get("href"))
        for interpreter_link in interpreter_links:
            interpreter_songs = requests.get("https://tanzschule-woelbing.de" + interpreter_link, proxies=PROXY)
            interpreter_songs_soup = BeautifulSoup(interpreter_songs.content, 'html.parser')
            for interpreter_song in interpreter_songs_soup.find("table", class_="table").find_all("tr"):
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
    except Exception as error:
        print("%s: %s" % ("Tanzschule Woelbing", error))
