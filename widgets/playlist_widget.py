import os
from pathlib import Path
from pprint import pprint
from typing import List

from PySide6 import QtWidgets
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTableView, QComboBox, QGridLayout, QPushButton, QFileDialog

from api.music.music_and_playlists_manager import MusicAndPlaylistsManager
from api.music.playlist_model import PlaylistModel
from api.music.playlist import Playlist
import config.config


class PlayListWidget(QtWidgets.QWidget):
    _base_dir: Path
    _playlist_view: QTableView
    _playlist_combo_box: QComboBox
    _delete_playlist_button: QPushButton
    _save_playlist_button: QPushButton
    _add_songs_button: QPushButton
    _layout: QGridLayout
    _playlists: List
    _music_and_playlists_manager: MusicAndPlaylistsManager
    _playlist_model: PlaylistModel

    def __init__(self, parent):
        super().__init__(parent)
        self._base_dir = self.parent()._base_dir
        self._music_and_playlists_manager = MusicAndPlaylistsManager()
        self._playlists = self._music_and_playlists_manager.get_all_playlists_from_store()
        self.setup_ui()
        self.populate_playlist_combo_box()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layout()
        self.add_widgets_layout()
        self.setup_connections()

    def create_widgets(self):
        self._playlist_model = PlaylistModel(self._playlists)
        self._playlist_view = QTableView(self)
        self._playlist_view.setModel(self._playlist_model)
        self._playlist_combo_box = QComboBox(self)
        self._delete_playlist_button = QPushButton(self)
        self._add_songs_button = QPushButton(self)
        self._save_playlist_button = QPushButton(self)

    def modify_widgets(self):
        save_icon = QIcon(os.path.join(self._base_dir, 'resources', 'disquette.png'))
        self._save_playlist_button.setIcon(save_icon)
        self._save_playlist_button.setToolTip("Sauvegarder la playlist")

        plus_icon = QIcon(os.path.join(self._base_dir, 'resources', 'plus.ico'))
        self._add_songs_button.setIcon(plus_icon)
        self._add_songs_button.setToolTip("Ajouter chanson(s) à la playlist courante")

        bin_icon = QIcon(os.path.join(self._base_dir, 'resources', 'bin.png'))
        self._delete_playlist_button.setIcon(bin_icon)
        self._delete_playlist_button.setToolTip("Supprimer la playlist courante")

        self._playlist_view.setShowGrid(False)
        self._playlist_view.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self._playlist_view.setColumnHidden(4, True)

    def create_layout(self):
        self._layout = QGridLayout(self)

    def add_widgets_layout(self):
        self._layout.addWidget(self._playlist_combo_box, 0, 0, 1, 3)
        self._layout.addWidget(self._delete_playlist_button, 0, 3, 1, 1)
        self._layout.addWidget(self._save_playlist_button, 0, 4, 1, 1)
        self._layout.addWidget(self._add_songs_button, 0, 5, 1, 1)
        self._layout.addWidget(self._playlist_view, 1, 0, -1, -1)

    def setup_connections(self):
        self._add_songs_button.clicked.connect(self.open_add_songs_dialog)
        self._save_playlist_button.clicked.connect(self.save_current_playlist)
        self._delete_playlist_button.clicked.connect(self.delete_current_playlist)
        self._playlist_combo_box.currentIndexChanged.connect(self._playlist_model.switch_playlist)

    def open_add_songs_dialog(self):
        dialog = QFileDialog(self, caption="Choose Music File(s) to add")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        dialog.setNameFilter("Music (*.mp3 *.ogg *.flac)")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        if dialog.exec():
            file_names = dialog.selectedFiles()
            self.add_songs_to_current_playlist(file_names)

    def populate_playlist_combo_box(self):
        [self._playlist_combo_box.addItem(x.name) for x in self._playlists]

    def save_current_playlist(self):
        index = self._playlist_combo_box.currentIndex()
        playlist = self._playlists[index]
        self._music_and_playlists_manager.save_one_playlist(playlist)

    def delete_current_playlist(self):
        print("Deleting current playlist...")

    def add_songs_to_current_playlist(self, p_files):
        if p_files is not None and len(p_files) > 0:
            print("Adding songs to current playlist...")
            pprint(p_files)
