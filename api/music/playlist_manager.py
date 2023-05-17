from pathlib import Path
import uuid

PLAYLIST_FILE_NAME_REGEX = ""

class PlaylistManager:
    _base_dir: Path
    _playlists: dict

    def __init__(self, p_base_dir):
        self._base_dir = p_base_dir
        self._playlists = {}

    def load_available_playlists(self):
        pass