import uuid
from typing import List
from datetime import datetime

from api.music.music_object import MusicObject


class Playlist:
    _uid: uuid.UUID
    _name: str
    _songs: List[uuid.UUID]
    _creation_time_stamp: datetime
    _is_dirty: bool

    def __init__(self, p_uid: str = None, p_name: str = None, p_creation_time_stamp = None):
        if p_uid is None:
            self.uid = uuid.uuid4()
        else:
            self.uid = uuid.UUID(p_uid)
        if p_name is None:
            self.name = "Nouvelle Playlist"
        else:
            self.name = p_name
        if p_creation_time_stamp is None:
            self.creation_date = datetime.now()
        else:
            self.creation_date = p_creation_time_stamp
        self.is_dirty = False
        self._songs = []

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
    def creation_date(self):
        return self._creation_time_stamp

    @creation_date.setter
    def creation_date(self, p_time_stamp):
        if isinstance(p_time_stamp, datetime):
            self._creation_time_stamp = p_time_stamp
        elif isinstance(p_time_stamp, float) and p_time_stamp > 0:
            self._creation_time_stamp = datetime.fromtimestamp(p_time_stamp)

    @property
    def is_dirty(self):
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, p_is_dirty):
        if isinstance(p_is_dirty, bool):
            self._is_dirty = p_is_dirty

    def size(self):
        return len(self._songs)

    def is_empty(self):
        return len(self._songs) == 0

    def get_all_songs(self):
        return self._songs

    def get_song(self, p_index):
        if 0 <= p_index < self.size():
            return self._songs[p_index]
        else:
            return None

    def add_song(self, p_uid: uuid.UUID, p_index: int = None):
        if p_index is None or p_index > len(self._songs):
            self._songs.append(p_uid)
        else:
            self._songs.insert(p_index, p_uid)
        self.is_dirty = True

    def add_songs(self, p_songs: List[MusicObject]):
        if len(p_songs) > 0:
            [self.add_song(x.uid) for x in p_songs]
            self.is_dirty = True

    def add_songs_at_index(self, p_songs: List[MusicObject], p_start_index: int):
        if len(p_songs) > 0:
            for i in range(len(p_songs)):
                self.add_song(p_songs[i].uid, p_start_index + i)

    def remove_song_by_index(self, p_index):
        if p_index < len(self._songs):
            del self._songs[p_index]
            self.is_dirty = True

    def remove_all_instances_of_song(self, p_uid: uuid.UUID):
        if p_uid is not None:
            nb_of_songs_before = self.size()
            self._songs = [x for x in self._songs if x != p_uid]
            nb_of_songs_after = self.size()
            if nb_of_songs_before != nb_of_songs_after:
                self.is_dirty = True

    def shift_one_song_up(self, p_index: int):
        if p_index > 0 and len(self._songs) >= 2:
            self._songs[p_index], self._songs[p_index - 1] = self._songs[p_index - 1], self._songs[p_index]
            self.is_dirty = True

    def shift_one_song_down(self, p_index: int):
        if p_index < len(self._songs) and len(self._songs) >= 2:
            self._songs[p_index], self._songs[p_index + 1] = self._songs[p_index + 1], self._songs[p_index]
            self.is_dirty = True
