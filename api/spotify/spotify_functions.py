import spotipy
import spotipy.util as sputil
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from api.util.singleton import Singleton

CLIENT_ID = "768db570dfb248d886aef6a02a5fe4b3"
CLIENT_SECRET = "b3ba00983c9a41ab87708dff3da3a5fe"
SCOPE = 'user-read-private user-read-playback-state user-modify-playback-state user-top-read playlist-modify-private playlist-modify-public user-library-read'
REDIRECT_URI = "http://localhost:8888/"


class SpotifyManager(Singleton):
    _client: spotipy.Spotify

    def initialize(self):
        auth_manager = SpotifyOAuth(scope=SCOPE, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI)
        self._client = spotipy.Spotify(auth_manager=auth_manager)

    def get_currently_playing_track(self):
        return self._client.currently_playing()

    def get_devices(self):
        return self._client.devices()

    def get_current_playlist(self):
        currently_playing = self._client.currently_playing()
        if currently_playing is not None:
            context = currently_playing["context"]
            if context is None:
                return None
            else:
                uri = context["uri"]
                playlist_id = uri.split(";")[-1]
                return self._client.playlist(playlist_id)