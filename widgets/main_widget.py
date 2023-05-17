import os

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QGridLayout, QStackedLayout, QLabel, QVBoxLayout, QCheckBox

from widgets.music_player import MusicPlayer
from widgets.playlist_widget import PlayListWidget
from widgets.timer_widget import MyTimerWidget


class MainWidget(QtWidgets.QWidget):
    _grid_main_layout: QGridLayout
    _photo: QLabel
    _playlist_widget: PlayListWidget
    _music_player: MusicPlayer
    _check_box_enable_match_and_break_transition: QCheckBox
    _check_box_enable_break_music: QCheckBox
    _match_timer_widget: MyTimerWidget
    _break_timer_widget: MyTimerWidget
    _base_dir: str

    def __init__(self, p_main_window):
        super().__init__(p_main_window)
        self._base_dir = p_main_window._base_dir
        self.setup_ui()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layout()
        self.add_widgets_layout()
        self.setup_connections()

    def create_widgets(self):
        self._photo = QLabel(self)
        self._playlist_widget = PlayListWidget(self)
        self._music_player = MusicPlayer(self)
        self._check_box_enable_match_and_break_transition = QCheckBox(self)
        self._check_box_enable_break_music = QCheckBox(self)
        self._match_timer_widget = MyTimerWidget(self, 300, "Match")
        self._break_timer_widget = MyTimerWidget(self, 300, "Break")

    def modify_widgets(self):
        # self._photo.setGeometry(QtCore.QRect(0, 0, 1769, 1324))
        # self._photo.setText("")
        # self._photo.setPixmap(
        #     QtGui.QPixmap(os.path.join(self.base_dir, 'resources', 'background', 'beach_volley_match_affiche.png')))
        # self._photo.setScaledContents(True)
        # self._photo.setObjectName("photo")
        self._check_box_enable_match_and_break_transition.setText("Transition match/pause automatique")
        self._check_box_enable_break_music.setText("Musique d'ambiance en dehors des matchs")
        self._break_timer_widget.setVisible(False)

    def create_layout(self):
        self._grid_main_layout = QGridLayout(self)

    def add_widgets_layout(self):
        self._grid_main_layout.addWidget(self._music_player, 0, 2, 1, 4)
        self._grid_main_layout.addWidget(self._playlist_widget, 0, 0, -1, 2)
        self._grid_main_layout.addWidget(self._match_timer_widget, 1, 2, 1, 2)
        self._grid_main_layout.addWidget(self._break_timer_widget, 1, 4, 1, 2)
        self._grid_main_layout.addWidget(self._check_box_enable_match_and_break_transition, 2, 2, 1, 2)
        self._grid_main_layout.addWidget(self._check_box_enable_break_music, 3, 2, 1, 2)

    def setup_connections(self):
        pass
