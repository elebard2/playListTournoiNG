import os
import random
import uuid
from pathlib import Path
from pprint import pprint
from typing import List

from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QIcon, QPalette, QColor, QShortcut, QKeySequence
from PySide6.QtWidgets import QTableView, QComboBox, QGridLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QFrame, \
    QMessageBox

from api.music.music_and_playlists_manager import MusicAndPlaylistsManager
from api.music.playlist_model import PlaylistModel
from api.music.playlist import Playlist


class PlayListWidget(QtWidgets.QWidget):
    signal_file_to_play = QtCore.Signal(str, int)
    signal_playlist_switched = QtCore.Signal()

    _base_dir: Path
    _playlist_view: QTableView
    _playlist_combo_box: QComboBox
    _delete_playlist_button: QPushButton
    _save_playlist_button: QPushButton
    _add_songs_button: QPushButton
    _new_playlist_label: QLabel
    _new_playlist_line_edit: QLineEdit
    _new_playlist_push_button: QPushButton
    _frame: QFrame
    _layout: QGridLayout
    _music_and_playlists_manager: MusicAndPlaylistsManager
    _playlist_model: PlaylistModel
    _delete_song_shortcut: QShortcut

    def __init__(self, parent):
        super().__init__(parent)
        self._base_dir = self.parent()._base_dir
        self._music_and_playlists_manager = MusicAndPlaylistsManager()
        self.setup_ui()
        self.populate_playlist_combo_box()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layout()
        self.add_widgets_layout()
        self.setup_connections()

    def create_widgets(self):
        self._playlist_model = PlaylistModel()
        self._playlist_view = QTableView(self)
        self._playlist_view.setModel(self._playlist_model)
        self._playlist_combo_box = QComboBox(self)
        self._delete_playlist_button = QPushButton(self)
        self._add_songs_button = QPushButton(self)
        self._save_playlist_button = QPushButton(self)
        self._new_playlist_label = QLabel(self)
        self._new_playlist_line_edit = QLineEdit(self)
        self._new_playlist_push_button = QPushButton(self)
        self._frame = QFrame(self)

    def modify_widgets(self):
        save_icon = QIcon(os.path.join(self._base_dir, 'resources', 'disquette.png'))
        self._save_playlist_button.setIcon(save_icon)
        self._save_playlist_button.setToolTip("Sauvegarder la playlist")
        self._save_playlist_button.setEnabled(False)

        plus_icon = QIcon(os.path.join(self._base_dir, 'resources', 'plus.ico'))
        self._add_songs_button.setIcon(plus_icon)
        self._add_songs_button.setToolTip("Ajouter chanson(s) à la playlist courante")
        self._add_songs_button.setEnabled(False)

        bin_icon = QIcon(os.path.join(self._base_dir, 'resources', 'bin.png'))
        self._delete_playlist_button.setIcon(bin_icon)
        self._delete_playlist_button.setToolTip("Supprimer la playlist courante")
        self._delete_playlist_button.setEnabled(False)

        self._playlist_view.setShowGrid(False)
        self._playlist_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self._playlist_view.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragDrop)
        self._playlist_view.setColumnHidden(4, True)
        self._playlist_view.setEnabled(False)

        self._new_playlist_label.setText("Nom de nouvelle playlist :")
        self._new_playlist_line_edit.setText("Nouvelle Playlist")

        self._new_playlist_push_button.setIcon(plus_icon)
        self._new_playlist_push_button.setToolTip("Initialiser une nouvelle playlist")

        self._frame.setLineWidth(5)
        self._frame.setMidLineWidth(1)
        self._frame.setFrameShape(QFrame.Shape.HLine)
        self._frame.setFrameShadow(QFrame.Shadow.Raised)
        self._frame.setPalette(QPalette(QColor(0, 127, 255, 127)))

        self._delete_song_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), self._playlist_view)

    def create_layout(self):
        self._layout = QGridLayout(self)

    def add_widgets_layout(self):
        self._layout.addWidget(self._new_playlist_label, 0, 0, 1, 1)
        self._layout.addWidget(self._new_playlist_line_edit, 0, 1, 1, 4)
        self._layout.addWidget(self._new_playlist_push_button, 0, 5, 1, 1)
        self._layout.addWidget(self._frame, 1, 0, 1, -1)
        self._layout.addWidget(self._playlist_combo_box, 2, 0, 1, 3)
        self._layout.addWidget(self._delete_playlist_button, 2, 3, 1, 1)
        self._layout.addWidget(self._save_playlist_button, 2, 4, 1, 1)
        self._layout.addWidget(self._add_songs_button, 2, 5, 1, 1)
        self._layout.addWidget(self._playlist_view, 3, 0, -1, -1)

    def setup_connections(self):
        self._add_songs_button.clicked.connect(self.open_add_songs_dialog)
        self._save_playlist_button.clicked.connect(self.save_current_playlist)
        self._delete_playlist_button.clicked.connect(self.delete_current_playlist)
        self._playlist_combo_box.currentIndexChanged.connect(self._playlist_model.switch_playlist)
        self._new_playlist_line_edit.textEdited.connect(self.handle_new_playlist_name_edited)
        self._new_playlist_push_button.clicked.connect(self.handle_new_playlist_button_clicked)
        self._playlist_view.doubleClicked.connect(self.handle_view_double_clicked)
        self._delete_song_shortcut.activated.connect(self.handle_delete_song)
        self._playlist_model.signal_no_playlist_selected.connect(self.handle_no_playlist)
        self._playlist_model.playlist_switched.connect(self.handle_playlist_switched)

    def open_add_songs_dialog(self):
        dialog = QFileDialog(self, caption="Choose Music File(s) to add")
        dialog.setViewMode(QFileDialog.ViewMode.Detail)
        dialog.setNameFilter("Music (*.mp3 *.ogg *.flac)")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        if dialog.exec():
            file_names = dialog.selectedFiles()
            self.add_songs_to_current_playlist(file_names)

    def populate_playlist_combo_box(self):
        all_available_playlists = self._music_and_playlists_manager.get_all_playlists_from_store()
        if len(all_available_playlists) > 0:
            [self._playlist_combo_box.addItem(x.name) for x in all_available_playlists]
            self._save_playlist_button.setEnabled(True)
            self._add_songs_button.setEnabled(True)
            self._delete_playlist_button.setEnabled(True)
            self._playlist_view.setEnabled(True)
            self._playlist_combo_box.setCurrentIndex(0)

    def save_current_playlist(self):
        index = self._playlist_combo_box.currentIndex()
        all_available_playlists = self._music_and_playlists_manager.get_all_playlists_from_store()
        playlist = all_available_playlists[index]
        self._music_and_playlists_manager.save_one_playlist(playlist.uid)

    def delete_current_playlist(self):
        index = self._playlist_combo_box.currentIndex()
        if index != -1:
            msg_box = QMessageBox(QMessageBox.Icon.Warning, "Confirmer suppression",
                                  "Voulez-vous vraiment supprimmer cette playlist ?")
            msg_box.setWindowIcon(QIcon(os.path.join(self._base_dir, 'resources', 'appIcon', 'beach_volley_icon.ico')))
            msg_box.setInformativeText("Attention : toute suppression est définitive")
            yes_button = msg_box.addButton(QMessageBox.StandardButton.Yes)
            no_button = msg_box.addButton(QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(no_button)
            msg_box.exec()
            if msg_box.clickedButton() == yes_button:
                print("Yes clicked - Deleting playlist")
                self._playlist_combo_box.removeItem(index)

    def add_songs_to_current_playlist(self, p_files: List[Path]):
        if p_files is not None and len(p_files) > 0:
            music_objects = [self._music_and_playlists_manager.add_music_to_store(Path(x)) for x in p_files]
            self._playlist_model.insert_songs_rows(music_objects, self._playlist_model.rowCount(), modify_current_playlist=True)

    def handle_new_playlist_name_edited(self):
        text = self._new_playlist_line_edit.text()
        if len(text) == 0:
            self._new_playlist_push_button.setEnabled(False)
        else:
            self._new_playlist_push_button.setEnabled(True)

    def handle_new_playlist_button_clicked(self):
        new_playlist_name = self._new_playlist_line_edit.text()
        new_playlist = Playlist(p_name=new_playlist_name)
        self._music_and_playlists_manager.put_playlist_in_store(new_playlist)
        nb_of_playlists = self._music_and_playlists_manager.get_number_of_playlists_in_store()
        self._playlist_combo_box.addItem(new_playlist_name)
        self._save_playlist_button.setEnabled(True)
        self._add_songs_button.setEnabled(True)
        self._delete_playlist_button.setEnabled(True)
        self._playlist_view.setEnabled(True)
        self._playlist_combo_box.setCurrentIndex(nb_of_playlists - 1)

    def handle_view_double_clicked(self, p_index: QModelIndex):
        if p_index.isValid():
            music_path = self._playlist_model.data_for_music_player(index=p_index)
            self.signal_file_to_play.emit(music_path, p_index.row())

    def handle_delete_song(self):
        index = self._playlist_view.currentIndex()
        if index.isValid():
            self._playlist_model.remove_songs_rows(1, index.row(), modify_current_playlist=True)

    def handle_playlist_switched(self):
        self.signal_playlist_switched.emit()

    def handle_no_playlist(self):
        self._playlist_combo_box.setEnabled(False)
        self._add_songs_button.setEnabled(False)
        self._delete_playlist_button.setEnabled(False)
        self._playlist_view.setEnabled(False)

    def handle_music_started_or_resumed(self):
        self._playlist_combo_box.setEnabled(False)
        self._delete_playlist_button.setEnabled(False)
        self._new_playlist_push_button.setEnabled(False)

    def handle_music_stopped(self):
        self._playlist_combo_box.setEnabled(True)
        self._delete_playlist_button.setEnabled(self._playlist_combo_box.count() > 0 and self._playlist_combo_box.currentIndex() != -1)
        self._new_playlist_push_button.setEnabled(True)

    def handle_change_track(self, p_repeat_mode: int, p_shuffle_mode: int, p_position: int, p_increment: int):
        current_playlist = self._playlist_model.get_playlist()
        if current_playlist is None:
            return
        current_playlist_size = current_playlist.size()
        if current_playlist_size <= 1:
            return
        if p_repeat_mode == 2:
            self.signal_file_to_play.emit(str(self._music_and_playlists_manager.get_music_from_store(current_playlist.get_song(p_position)).path), p_position)
        elif p_shuffle_mode == 1:
            new_position = p_position + p_increment
            if 0 <= new_position < current_playlist_size:
                self.signal_file_to_play.emit(
                    str(self._music_and_playlists_manager.get_music_from_store(current_playlist.get_song(new_position)).path),
                    new_position)
            elif p_repeat_mode == 1 and new_position < 0 or new_position >= current_playlist_size:
                shifted_position = new_position % current_playlist_size
                self.signal_file_to_play.emit(
                    str(self._music_and_playlists_manager.get_music_from_store(current_playlist.get_song(shifted_position)).path),
                    shifted_position)
        elif p_shuffle_mode == 2:
            new_position = random.choice([i for i in range(current_playlist_size-1) if i not in [p_position]])
            self.signal_file_to_play.emit(
                str(self._music_and_playlists_manager.get_music_from_store(current_playlist.get_song(new_position)).path),
                new_position)

    def handle_first_click_on_play(self):
        current_playlist = self._playlist_model.get_playlist()
        if current_playlist is None:
            return
        current_playlist_size = current_playlist.size()
        if current_playlist_size == 0:
            return
        self.signal_file_to_play.emit(
            str(self._music_and_playlists_manager.get_music_from_store(current_playlist.get_song(0)).path),
            0)