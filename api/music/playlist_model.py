from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List

import api.music.playlist
from api.music.music_and_playlists_manager import MusicAndPlaylistsManager
from api.music.music_object import MusicObject
from api.music.playlist import Playlist


class PlaylistModel(QAbstractTableModel):
    _headers = ["Numéro", "Titre", "Durée", "Artiste", "Path"]
    _available_playlists: List[Playlist]
    _current_playlist: Playlist
    _music_and_playlist_manager: MusicAndPlaylistsManager

    def __init__(self, p_playlists: List[Playlist]=None):
        super().__init__()
        self._current_playlist = Playlist()
        self._available_playlists = p_playlists
        self._music_and_playlist_manager = MusicAndPlaylistsManager()
        [self.setHeaderData(i, Qt.Orientation.Horizontal, self._headers[i]) for i in range(len(self._headers))]
        if self._available_playlists is not None and len(self._available_playlists) > 0:
            self.set_playlist(self._available_playlists[0])

    def rowCount(self, parent=None):
        return self._current_playlist.size()

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            music_uid = self._current_playlist.get_song(index.row())
            music = self._music_and_playlist_manager.get_music_from_store(music_uid)
            c = index.column()
            if c == 0:
                return index.row() + 1
            elif c == 1:
                return music.title
            elif c == 2:
                d = music.format_duration()
                return d
            elif c == 3:
                return music.artist
            elif c == 4:
                return str(music.path)
        else:
            return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        else:
            return None

    def insertSongs(self, songs: List[MusicObject], index_start: int = 0):
        if self._current_playlist.is_empty() or 0 <= index_start < self._current_playlist.size():
            super().beginInsertRows(QModelIndex(), index_start, index_start + len(songs))
            super().endInsertRows()

    def removeSongs(self, count: int, row: int = 0):
        if 0 <= row <= self.rowCount() and count <= self.rowCount() - row:
            super().beginRemoveRows(QModelIndex(), row, row + count)
            super().endRemoveRows()

    def get_playlist(self):
        return self._current_playlist

    def switch_playlist(self, index):
        new_playlist = self._available_playlists[index]
        self.set_playlist(new_playlist)

    def set_playlist(self, p_playlist):
        self._current_playlist = p_playlist
        if isinstance(p_playlist, api.music.playlist.Playlist):
            self.populate_model()

    def populate_model(self):
        if self.rowCount() > 0:
            self.removeSongs(self.rowCount())
        self.insertSongs(self._current_playlist.get_all_songs())
