import json
import uuid
from pathlib import Path
from typing import List

from api.music.music_exceptions import NotAMusicFileError, MusicLoadError
from api.music.music_object import MusicObject


class Playlist:
    _uid: uuid.UUID
    _name: str
    _songs_raw_data: list
    _songs: List[MusicObject]
    _save_path: Path
    _is_dirty: bool
    _is_lazy_loaded: bool
    _is_fully_loaded: bool

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, p_uid):
        self._uid = p_uid

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, p_name):
        self._name = p_name

    @property
    def save_path(self):
        return self._save_path

    @save_path.setter
    def save_path(self, p_save_path):
        self._save_path = p_save_path

    @property
    def is_dirty(self):
        return self._is_dirty

    def __init__(self, p_path_to_playlist_file: Path = None, p_lazy_load=True):
        self._uid = uuid.uuid4()
        self._name = f"Playlist_{str(self._uid)[0:8]}"
        self._songs = []
        self._is_dirty = False
        self._is_lazy_loaded = p_lazy_load
        self._is_fully_loaded = not p_lazy_load
        self._songs_raw_data = []
        if p_path_to_playlist_file is not None:
            self.load_from_file(p_path_to_playlist_file, p_lazy_load)

    def load_from_file(self, p_path_to_playlist_file, p_lazy_load):
        if p_path_to_playlist_file is not None:
            f = open(p_path_to_playlist_file, "r")
            data = json.loads(f.read())
            self._save_path = p_path_to_playlist_file
            self._name = data['name']
            self._uid = data['uuid']
            songs = data['songs']
            self._songs_raw_data = songs
            self._is_lazy_loaded = p_lazy_load
            self._is_fully_loaded = not p_lazy_load
            if not self._is_lazy_loaded:
                self.load_songs_from_raw_data()

    def finish_loading(self):
        if self._is_lazy_loaded and len(self._songs_raw_data) > 0:
            self.load_songs_from_raw_data()

    def load_songs_from_raw_data(self):
        for song in self._songs_raw_data:
            try:
                music_object = MusicObject(Path(song['path']))
                self._songs.append(music_object)
            except NotAMusicFileError:
                self._is_dirty = True
                continue
            except MusicLoadError:
                self._is_dirty = True
                continue

    def remove_song(self, index):
        if index < len(self._songs):
            del self._songs[index]
