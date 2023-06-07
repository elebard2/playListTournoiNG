from PySide6 import QtCore
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import List

import api.music.playlist
from api.music.music_and_playlists_manager import MusicAndPlaylistsManager
from api.music.music_object import MusicObject
from api.music.playlist import Playlist


class PlaylistModel(QAbstractTableModel):
    signal_no_playlist_selected = QtCore.Signal()
    playlist_switched = QtCore.Signal()

    _headers = ["Numéro", "Titre", "Durée", "Artiste", "Path"]
    _current_playlist: Playlist
    _music_and_playlist_manager: MusicAndPlaylistsManager

    def __init__(self):
        super().__init__()
        self.set_playlist(None)
        self._music_and_playlist_manager = MusicAndPlaylistsManager()
        available_playlists = self._music_and_playlist_manager.get_all_playlists_from_store()
        [self.setHeaderData(i, Qt.Orientation.Horizontal, self._headers[i]) for i in range(len(self._headers))]
        if available_playlists is not None and len(available_playlists) > 0:
            self.set_playlist(available_playlists[0])

    def rowCount(self, parent=None):
        if self._current_playlist is None:
            return 0
        else:
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

    def data_for_music_player(self, index: QModelIndex):
        if index.isValid():
            music_uid = self._current_playlist.get_song(index.row())
            music = self._music_and_playlist_manager.get_music_from_store(music_uid)
            return str(music.path)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        else:
            return None

    def insert_songs_rows(self, songs: List[MusicObject], index_start: int = 0, modify_current_playlist: bool = False):
        if self.get_playlist() is not None and self.get_playlist().is_empty() or 0 <= index_start < self.get_playlist().size():
            super().beginInsertRows(QModelIndex(), index_start, index_start + len(songs))
            if modify_current_playlist:
                self.insertRows(index_start, len(songs))
                self._current_playlist.add_songs_at_index(songs, index_start)
            super().endInsertRows()

    def remove_songs_rows(self, count: int, row: int = 0, modify_current_playlist: bool = False):
        if 0 <= row <= self.rowCount() and count <= self.rowCount() - row:
            super().beginRemoveRows(QModelIndex(), row, row + count)
            if modify_current_playlist:
                self.removeRows(row, count)
                for _ in range(count):
                    self._current_playlist.remove_song_by_index(row)
            super().endRemoveRows()

    def get_playlist(self):
        return self._current_playlist

    def set_playlist(self, p_playlist):
        self._current_playlist = p_playlist
        if isinstance(p_playlist, api.music.playlist.Playlist):
            self.populate_model()
        else:
            self.removeRows(0, self.rowCount())
            self.signal_no_playlist_selected.emit()

    def switch_playlist(self, index):
        available_playlists = self._music_and_playlist_manager.get_all_playlists_from_store()
        if 0 <= index < len(available_playlists):
            new_playlist = available_playlists[index]
            self.set_playlist(new_playlist)
            self.playlist_switched.emit()

    def populate_model(self):
        if self.rowCount() > 0:
            self.remove_songs_rows(self.rowCount())
        self.insert_songs_rows(self._current_playlist.get_all_songs())
