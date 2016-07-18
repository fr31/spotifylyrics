'''
    * You'll need to download xmltodict and BeautifulSoup
    * Easiest method to do so: "(sudo) pip install pycurl xmltodict BeautifulSoup json"

    * ViewLyrics Open Searcher
    * Developed by PedroHLC
    * Converted to python by Rikels
    * Updated to Python 3 by fr31
    * Last update: 18-07-2016

    * lyricswikia Lyric returner
    * Developed by Rikels
    * Last update: 18-07-2016
'''

import hashlib
import json
try:
    import xmltodict
except:
    SystemExit("can\'t find xmltodict, please install it via \"pip install xmltodict\"")

try:
    import requests
except:
    SystemExit("can\'t find reuqests, please install it via \"pip install requests\"")

try:
    from BeautifulSoup import BeautifulSoup
except:
    try:
        from  bs4 import BeautifulSoup
    except:
        SystemExit("can\'t find BeautifulSoup, please install it via \"pip install BeautifulSoup\"")

import re

# function to return python workable results from Minilyrics
def MiniLyrics(artist, title):
    search_url = "http://search.crintsoft.com/searchlyrics.htm"
    search_query_base = "<?xml version='1.0' encoding='utf-8' standalone='yes' ?><searchV1 client=\"ViewLyricsOpenSearcher\" artist=\"{artist}\" title=\"{title}\" OnlyMatched=\"1\" />"
    search_useragent = "MiniLyrics"
    search_md5watermark = b"Mlv1clt4.0"

    # hex is a registered value in python, so i used hexx as an alternative
    def hexToStr(hexx):
        string = ''
        i = 0
        while (i < (len(hexx) - 1)):
            string += chr(int(hexx[i] + hexx[i + 1], 16))
            i += 2
        return (string)

    def vl_enc(data, md5_extra):
        datalen = len(data)
        md5 = hashlib.md5()
        md5.update(data + md5_extra)
        hasheddata = hexToStr(md5.hexdigest())
        j = 0
        i = 0
        while (i < datalen):
            try:
                j += data[i]
            except TypeError:
                j += ord(data[i])
            i += 1
        magickey = chr(int(round(float(j) / float(datalen))))
        encddata = list(range(len(data)))
        if isinstance(magickey, int):
            pass
        else:
            magickey = ord(magickey)
        for i in range(datalen):
            # Python doesn't do bitwise operations with characters, so we need to convert them to integers first.
            # It also doesn't like it if you put integers in the ord() to be translated to integers, that's what the IF, ELSE is for.
            if isinstance(data[i], int):
                encddata[i] = data[i] ^ magickey
            else:
                encddata[i] = ord(data[i]) ^ magickey
        try:
            result = "\x02" + chr(magickey) + "\x04\x00\x00\x00" + str(hasheddata) + bytearray(encddata).decode("utf-8")
        except UnicodeDecodeError:
            result = "\x02" + chr(magickey) + "\x04\x00\x00\x00" + str(hasheddata) + bytearray(encddata)
        return (result)

    search_encquery = vl_enc(search_query_base.format(artist=artist, title=title).encode("utf-8"), search_md5watermark)

    def http_post(url, data, ua):
        headers = {"User-Agent": "{ua}".format(ua=ua),
                   "Content-Length": "{content_length}".format(content_length=len(data)),
                   "Connection": "Keep-Alive",
                   "Expect": "100-continue",
                   "Content-Type": "application/x-www-form-urlencoded"
                   }
        # trying to keep the script as sturdy as possible
        try:
            r = requests.post(url, data=data, headers=headers)
            return (r.text)
        except Exception as exceptio:
            print(exceoptio)
            pass
        # if the request was denied, or the connection was interrupted, retrying. (up to five times)
        fail_count = 0
        while (r.text == "") and (fail_count < 5):
            fail_count += 1
            print(("buffer was empty, retry time: {fails}".format(fails=fail_count)))
            try:
                r = requests.post(url, data=data, headers=headers)
            except:
                pass
            if fail_count >= 5:
                print("didn't receive anything from the server, check the connection...")
                return

    try:
        search_result = http_post(search_url, search_encquery, search_useragent);
    except:
        print("something went wrong, could be a lot of things :(")

    def vl_dec(data):
        magickey = data[1]
        result = ""
        i = 22
        datalen = len(data)
        if isinstance(magickey, int):
            pass
        else:
            magickey = ord(magickey)
        for i in range(22, datalen):
            # python doesn't do bitwise operations with characters, so we need to convert them to integers first.
            if isinstance(data[i], int):
                result += chr(data[i] ^ magickey)
            else:
                result += chr(ord(data[i]) ^ magickey)
        return (result)

    if ('search_result' not in locals()):
        # didn't receive a reply from the server
        print("FAILED")
        return ("Script might be broken :(")
    else:
        # Server returned possible answers
        xml = vl_dec(search_result)
        xml = xmltodict.parse(xml)
        server_url = str(xml["return"]["@server_url"])
        results = []
        i = 0
        if isinstance(xml["return"]["fileinfo"], list):
            for item in xml["return"]["fileinfo"]:
                # because the rating will sometimes not be filled, it could give an error, so the rating will be 0 for unrated items
                try:
                    rating = item["@rate"]
                except:
                    rating = 0
                try:
                    artist = item["@artist"]
                except:
                    artist = None
                try:
                    title = item["@title"]
                except:
                    title = None
                results.append({'artist': artist, 'title': title, 'rating': float(rating),
                                'filetype': item["@link"].split(".")[-1], 'url': (server_url + item["@link"])})
                i += 1
            results = sorted(results, key=lambda result: (result["rating"]))
            results.reverse()
        else:
            # because the rating will sometimes not be filled, it could give an error, so the rating will be 0 for unrated items
            try:
                rating = xml["return"]["fileinfo"]["@rate"]
            except:
                rating = 0
            try:
                artist = xml["return"]["fileinfo"]["@artist"]
            except:
                artist = None
            try:
                title = xml["return"]["fileinfo"]["@title"]
            except:
                title = None
            results.append({'artist': artist, 'title': title, 'rating': float(rating),
                            'filetype': xml["return"]["fileinfo"]["@link"].split(".")[-1],
                            'url': (server_url + xml["return"]["fileinfo"]["@link"])})
    return(results)

# function to return lyrics grabbed from lyricwikia
def LyricWikia(artist, title):
    url = 'http://lyrics.wikia.com/api.php?action=lyrics&artist={artist}&song={title}&fmt=json&func=getSong'.format(artist=artist,
                                                                                                                    title=title).replace(" ","%20")
    r = requests.get(url, timeout=15)
    # We got some bad formatted JSON data... So we need to fix stuff :/
    returned = r.text
    returned = returned.replace("\'", "\"")
    returned = returned.replace("song = ", "")
    returned = json.loads(returned)
    if returned["lyrics"] != "Not found":
        # set the url to the url we just recieved, and retrieving it
        r = requests.get(returned["url"], timeout=15)
        soup = BeautifulSoup(r.text)
        soup = soup.find("div", {"class": "lyricbox"})
        [elem.extract() for elem in soup.findAll('div')]
        [elem.replaceWith('\n') for elem in soup.findAll('br')]
        #with old BeautifulSoup the following is needed..? For recent versions, this isn't needed/doesn't work
        try:
            soup = BeautifulSoup(str(soup), convertEntities=BeautifulSoup.HTML_ENTITIES)
        except:
            pass
        soup = BeautifulSoup(re.sub(r'(<!--[.\s\S]*-->)', '', str(soup)))
        [elem.extract() for elem in soup.findAll('script')]
        return(soup.getText())
    else:
        return()