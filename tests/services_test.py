import os
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

    services_to_test = [
        services._minilyrics,
        services._wikia,
        services._musixmatch,
        services._songmeanings,
        services._songlyrics,
        services._genius,
        services._versuri
    ]

    def test_services(self):
        for service in self.services_to_test:
            for song in self.songs:
                path = os.path.abspath("res/" + song.artist.lower() + " - " + song.name.lower())
                with open(path, "rb") as lyrics_words:
                    result = service(song)

                    self.assertTrue(any(x in result[0].lower() for x in pickle.load(lyrics_words)))
