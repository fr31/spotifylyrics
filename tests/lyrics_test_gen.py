import pickle

import pylrc

import backend
import services


def split_to_word(string):
    return string.replace("\n", " ").replace("\r", " ").split(" ")


if __name__ == "__main__":
    ARTIST = input("Artist: ")
    TITLE = input("Title: ")

    SONG = backend.Song(ARTIST, TITLE)
    LYRICS = []

    SONG_ON_ALL_SERVICES = True

    if SONG_ON_ALL_SERVICES:
        for service in backend.SERVICES_LIST1:
            result = service(SONG)
            if result[0] == services.ERROR:
                SONG_ON_ALL_SERVICES = False
                break
            words = {x.lower() for x in split_to_word(" ".join(e.text for e in pylrc.parse(result[0]))) if x != ""}
            LYRICS.append(words)

    if SONG_ON_ALL_SERVICES:
        for service in backend.SERVICES_LIST2:
            result = service(SONG)
            if result[0] == services.ERROR:
                SONG_ON_ALL_SERVICES = False
                break
            words = {x.lower() for x in split_to_word(result[0]) if x != ""}
            LYRICS.append(words)

    print()
    if SONG_ON_ALL_SERVICES:
        COMMON_WORDS = LYRICS[0].intersection(*LYRICS[1:])
        print("Please validate that these words are all in the song text "
              "and that not too much words are not in the list")
        print(COMMON_WORDS)
        with open("res/" + ARTIST.lower() + " - " + TITLE.lower(), "wb") as words_file:
            pickle.dump(COMMON_WORDS, words_file)
    else:
        print("Song not on all services")
