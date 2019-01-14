import pickle
import unittest

import backend
import services


class LyricsTest(unittest.TestCase):
    """ Don't forget to run lyrics_test_gen.py """
    songs = [
        backend.Song("Queen", "We Will Rock You"),
        backend.Song("Michael Jackson", "Thriller")
    ]

    def test_minilyrics(self):
        for song in self.songs:
            with open("res/" + song.artist.lower() + " - " + song.name.lower(), "rb") as lyrics_words:
                self.assertTrue(any(x in services._minilyrics(song)[0].lower() for x in pickle.load(lyrics_words)))

    def test_wikia(self):
        for song in self.songs:
            with open("res/" + song.artist.lower() + " - " + song.name.lower(), "rb") as lyrics_words:
                self.assertTrue(any(x in services._wikia(song)[0].lower() for x in pickle.load(lyrics_words)))

    def test_musixmatch(self):
        for song in self.songs:
            with open("res/" + song.artist.lower() + " - " + song.name.lower(), "rb") as lyrics_words:
                self.assertTrue(any(x in services._musixmatch(song)[0].lower() for x in pickle.load(lyrics_words)))

    def test_songmeanings(self):
        for song in self.songs:
            with open("res/" + song.artist.lower() + " - " + song.name.lower(), "rb") as lyrics_words:
                self.assertTrue(any(x in services._songmeanings(song)[0].lower() for x in pickle.load(lyrics_words)))

    def test_songlyrics(self):
        for song in self.songs:
            with open("res/" + song.artist.lower() + " - " + song.name.lower(), "rb") as lyrics_words:
                self.assertTrue(any(x in services._songlyrics(song)[0].lower() for x in pickle.load(lyrics_words)))

    def test_genius(self):
        for song in self.songs:
            with open("res/" + song.artist.lower() + " - " + song.name.lower(), "rb") as lyrics_words:
                self.assertTrue(any(x in services._genius(song)[0].lower() for x in pickle.load(lyrics_words)))

    def test_versuri(self):
        for song in self.songs:
            with open("res/" + song.artist.lower() + " - " + song.name.lower(), "rb") as lyrics_words:
                self.assertTrue(any(x in services._versuri(song)[0].lower() for x in pickle.load(lyrics_words)))
