import json
import uuid
from pathlib import Path
from typing import List

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

from api.music.music_exceptions import NotAMusicFileError, MusicLoadError
from api.music.music_object import MusicObject


class PlaylistModel(QAbstractTableModel):
    _path_to_playlist_file: Path
    _name: str
    _id: uuid.UUID
    _songs: List[MusicObject]

    def __init__(self, p_path_to_playlist_file=None):
        super().__init__()
        self.setHeaderData(0, Qt.Orientation.Horizontal, "Numéro")
        self.setHeaderData(1, Qt.Orientation.Horizontal, "Titre")
        self.setHeaderData(2, Qt.Orientation.Horizontal, "Durée")
        self.setHeaderData(3, Qt.Orientation.Horizontal, "Artiste")
        self.setHeaderData(4, Qt.Orientation.Horizontal, "Supprimer")
        self._songs = list()
        if p_path_to_playlist_file is not None:
            self.path = p_path_to_playlist_file
            self.try_loading_playlist_from_file()
        else:
            self.uid = uuid.uuid4()
            self.name = f"Playlist_{str(self._id)[0:8]}"

    @property
    def path(self):
        return self._path_to_playlist_file

    @path.setter
    def path(self, p_path):
        if isinstance(p_path, Path) and p_path.suffix == ".json":
            self._path_to_playlist_file = p_path

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, p_name):
        if isinstance(p_name, str):
            self._name = p_name

    @property
    def uid(self):
        return self._id

    @uid.setter
    def uid(self, p_uuid):
        if isinstance(p_uuid, uuid.UUID):
            self._id = p_uuid

    def try_loading_playlist_from_file(self):
        if self.path is not None:
            f = open(self.path, "r")
            data = json.loads(f.read())
            self.name = data['name']
            self.uid = data['uuid']
            songs = data['songs']
            for song in songs:
                try:
                    music_object = MusicObject(Path(song['path']))
                    self._songs.append(music_object)
                except NotAMusicFileError:
                    continue
                except MusicLoadError:
                    continue

    def rowCount(self, index):
        return len(self._songs)

    def columnCount(self, index):
        return 5

    def data(self, index, role):
        if role == Qt.DisplayRole:
            status, text = self._songs[index.row()]
            return text

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section == 0:
                    return "Numéro"
                elif section == 1:
                    return "Titre"
                elif section == 2:
                    return "Durée"
                elif section == 3:
                    return "Artiste"
                elif section == 4:
                    return "Supprimer"
            else:
                return ""