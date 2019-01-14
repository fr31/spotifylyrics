import pickle

import pylrc

import backend
import services


def split_to_word(s):
    return s.replace("\n", " ").replace("\r", " ").split(" ")


if __name__ == "__main__":
    artist = input("Artist: ")
    title = input("Title: ")

    song = backend.Song(artist, title)
    lyrics = []

    song_on_all_services = True

    if song_on_all_services:
        for service in backend.services_list1:
            result = service(song)
            if result[0] == services.error:
                song_on_all_services = False
                break
            words = set([x.lower() for x in split_to_word(" ".join(e.text for e in pylrc.parse(result[0]))) if x != ""])
            lyrics.append(words)

    if song_on_all_services:
        for service in backend.services_list2:
            result = service(song)
            if result[0] == services.error:
                song_on_all_services = False
                break
            words = set([x.lower() for x in split_to_word(result[0]) if x != ""])
            lyrics.append(words)

    print()
    if song_on_all_services:
        common_words = lyrics[0].intersection(*lyrics[1:])
        print("Please validate that these words are all in the song text "
              "and that not too much words are not in the list")
        print(common_words)
        with open("res/" + artist.lower() + " - " + title.lower(), "wb") as words_file:
            pickle.dump(common_words, words_file)
    else:
        print("Song not on all services")
