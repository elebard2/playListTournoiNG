import os
from pathlib import Path

from PySide6 import QtWidgets
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTableView, QComboBox, QGridLayout, QPushButton

from api.music.playlist_model import PlaylistModel


class PlayListWidget(QtWidgets.QWidget):
    _base_dir: Path
    _playlist_view: QTableView
    _playlist_combo_box: QComboBox
    _save_playlist_button: QPushButton
    _add_songs_button: QPushButton
    _layout: QGridLayout

    def __init__(self, parent):
        super().__init__(parent)
        self._base_dir = self.parent()._base_dir
        self.setup_ui()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layout()
        self.add_widgets_layout()
        self.setup_connections()

    def create_widgets(self):
        model = PlaylistModel()
        self._playlist_view = QTableView(self)
        self._playlist_view.setModel(model)
        self._playlist_combo_box = QComboBox(self)
        self._add_songs_button = QPushButton(self)
        self._save_playlist_button = QPushButton(self)

    def modify_widgets(self):
        save_icon = QIcon(os.path.join(self._base_dir, 'resources', 'disquette.png'))
        self._save_playlist_button.setIcon(save_icon)
        self._save_playlist_button.setToolTip("Sauvegarder la playlist")

        plus_icon = QIcon(os.path.join(self._base_dir, 'resources', 'plus.ico'))
        self._add_songs_button.setIcon(plus_icon)
        self._add_songs_button.setToolTip("Ajouter chanson(s) à la playlist")

    def create_layout(self):
        self._layout = QGridLayout(self)

    def add_widgets_layout(self):
        self._layout.addWidget(self._playlist_combo_box, 0, 0, 1, 3)
        self._layout.addWidget(self._save_playlist_button, 0, 3, 1, 1)
        self._layout.addWidget(self._add_songs_button, 0, 4, 1, 1)
        self._layout.addWidget(self._playlist_view, 1, 0, -1, -1)

    def setup_connections(self):
        pass
