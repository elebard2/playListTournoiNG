from enum import Enum

from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QGridLayout, QLabel, QCheckBox, QPushButton, QWidget

from api.music.music_and_playlists_manager import MusicAndPlaylistsManager
from widgets.music_player import MusicPlayer
from widgets.playlist_widget import PlayListWidget
from widgets.timer_widget import MyTimerWidget


class TimerChainingMode(Enum):
    NO_CYCLING = 1
    CYCLING = 2


class MainWidget(QtWidgets.QWidget):
    toggle_mode_signal = QtCore.Signal(int)
    signal_ambient_music = QtCore.Signal(str)
    match_timer_ends = QtCore.Signal()
    break_timer_ends = QtCore.Signal(int)
    match_timer_stops = QtCore.Signal(int)
    break_timer_stops = QtCore.Signal(int)

    _mode: TimerChainingMode
    _grid_main_layout: QGridLayout
    _photo: QLabel
    _playlist_widget: PlayListWidget
    _music_player: MusicPlayer
    _check_box_enable_match_and_break_transition: QCheckBox
    _check_box_enable_break_music: QCheckBox
    _start_cycling_button: QPushButton
    _stop_cycling_button: QPushButton
    _empty_widget: QWidget
    _match_timer_widget: MyTimerWidget
    _break_timer_widget: MyTimerWidget
    _base_dir: str
    _music_and_playlists_manager: MusicAndPlaylistsManager

    def __init__(self, p_base_dir):
        super().__init__()
        self._base_dir = p_base_dir
        self._mode = TimerChainingMode.NO_CYCLING
        self._music_and_playlists_manager = MusicAndPlaylistsManager()
        self.setup_ui()

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, p_mode):
        if isinstance(p_mode, TimerChainingMode) or isinstance(p_mode, int):
            self._mode = TimerChainingMode(p_mode)
            self.toggle_mode_signal.emit(self._mode.value)

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
        self._start_cycling_button = QPushButton(self)
        self._stop_cycling_button = QPushButton(self)
        self._empty_widget = QWidget(self)
        self._match_timer_widget = MyTimerWidget(self, 300, 1)
        self._break_timer_widget = MyTimerWidget(self, 300, 2)

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
        self._start_cycling_button.setText("Démarrer cycle match/pause")
        self._start_cycling_button.setVisible(False)
        self._stop_cycling_button.setText("Arrêter cycle")
        self._stop_cycling_button.setVisible(False)
        self._stop_cycling_button.setEnabled(False)

    def create_layout(self):
        self._grid_main_layout = QGridLayout(self)

    def add_widgets_layout(self):
        self._grid_main_layout.setRowStretch(0, 12)
        self._grid_main_layout.setRowStretch(2, 18)
        self._grid_main_layout.setRowStretch(3, 6)
        self._grid_main_layout.setRowStretch(1, 1)
        self._grid_main_layout.addWidget(self._music_player, 0, 2, 1, 4)
        self._grid_main_layout.addWidget(self._playlist_widget, 0, 0, -1, 2)
        self._grid_main_layout.addWidget(self._check_box_enable_match_and_break_transition, 3, 3, 1, 2)
        self._grid_main_layout.addWidget(self._check_box_enable_break_music, 3, 4, 1, 2)
        self._grid_main_layout.addWidget(self._empty_widget, 1, 2, 1, 1)
        self._grid_main_layout.addWidget(self._start_cycling_button, 1, 3, 1, 1)
        self._grid_main_layout.addWidget(self._stop_cycling_button, 1, 4, 1, 1)
        self._grid_main_layout.addWidget(self._match_timer_widget, 2, 2, 1, 2)
        self._grid_main_layout.addWidget(self._break_timer_widget, 2, 4, 1, 2)

    def setup_connections(self):
        # Connect Cycling Buttons Signals
        self._start_cycling_button.clicked.connect(self._match_timer_widget.start_timer)
        self._start_cycling_button.clicked.connect(self.start_cycling_button_clicked)
        self._stop_cycling_button.clicked.connect(self.stop_cycling_button_clicked)
        self._stop_cycling_button.clicked.connect(self._match_timer_widget.stop_timer)
        self._stop_cycling_button.clicked.connect(self._break_timer_widget.stop_timer)

        # Connect CheckBoxes Signals
        self._check_box_enable_match_and_break_transition.stateChanged.connect(self.toggle_mode)
        self._check_box_enable_break_music.stateChanged.connect(self._music_player.toggle_mode)

        # Connect Match Timer Signals
        self._match_timer_widget.timer_starts.connect(self._music_player.handle_timer_starts)
        self._match_timer_widget.timer_specific_threshold.connect(self._music_player.handle_match_timer_threshold)
        self._match_timer_widget.timer_ends.connect(self.handle_timer_ends)
        self._match_timer_widget.timer_stops.connect(self.handle_timer_stops)

        # Connect Break Timer Signals
        self._break_timer_widget.timer_starts.connect(self._music_player.handle_timer_starts)
        self._break_timer_widget.timer_specific_threshold.connect(self._music_player.handle_break_timer_threshold)
        self._break_timer_widget.timer_ends.connect(self.handle_timer_ends)
        self._break_timer_widget.timer_stops.connect(self.handle_timer_stops)

        self._playlist_widget.signal_file_to_play.connect(self._music_player.handle_music_to_play_received)
        self._playlist_widget.signal_playlist_switched.connect(self._music_player.handle_playlist_switched)

        self._music_player.request_ambient_music_track.connect(self.handle_ambient_music_requested)
        self._music_player.music_started_or_resumed.connect(self._playlist_widget.handle_music_started_or_resumed)
        self._music_player.music_stopped.connect(self._playlist_widget.handle_music_stopped)
        self._music_player.change_track_button_clicked.connect(self._playlist_widget.handle_change_track)
        self._music_player.play_button_clicked.connect(self._playlist_widget.handle_first_click_on_play)

        # Connect own signals
        self.toggle_mode_signal.connect(self._match_timer_widget.switch_mode)

        self.match_timer_ends.connect(self._music_player.handle_match_timer_ends)
        self.match_timer_stops.connect(self._music_player.handle_match_timer_stops)

        self.break_timer_ends.connect(self._music_player.handle_break_timer_ends)
        self.break_timer_stops.connect(self._music_player.handle_break_timer_stops)

        self.signal_ambient_music.connect(self._music_player.handle_receive_ambient_music)

    def toggle_mode(self, state):
        if state == 2:
            self._break_timer_widget.setVisible(True)
            self._start_cycling_button.setVisible(True)
            self._stop_cycling_button.setVisible(True)
            self._match_timer_widget.timer_ends.connect(self._break_timer_widget.start_timer)
            self._break_timer_widget.timer_ends.connect(self._match_timer_widget.start_timer)
            self.mode = 2
        else:
            self._break_timer_widget.setVisible(False)
            self._start_cycling_button.setVisible(False)
            self._stop_cycling_button.setVisible(False)
            self._match_timer_widget.timer_ends.disconnect(self._break_timer_widget.start_timer)
            self._break_timer_widget.timer_ends.disconnect(self._match_timer_widget.start_timer)
            self.mode = 1

    def start_cycling_button_clicked(self):
        self._start_cycling_button.setEnabled(False)
        self._stop_cycling_button.setEnabled(True)
        self._check_box_enable_match_and_break_transition.setEnabled(False)
        self._check_box_enable_break_music.setEnabled(False)

    def stop_cycling_button_clicked(self):
        self._start_cycling_button.setEnabled(True)
        self._stop_cycling_button.setEnabled(False)
        self._check_box_enable_match_and_break_transition.setEnabled(True)
        self._check_box_enable_break_music.setEnabled(True)

    def handle_ambient_music_requested(self):
        ambient_music = self._music_and_playlists_manager.get_selected_ambient_music()
        if ambient_music is not None:
            self.signal_ambient_music.emit(str(ambient_music.path))

    def handle_timer_ends(self, p_id: int):
        if p_id == 1:
            self.match_timer_ends.emit()
        else:
            self.break_timer_ends.emit(self.mode.value)

    def handle_timer_stops(self, p_id: int, p_slave_mode: int):
        if p_id == 1:
            self.match_timer_stops.emit(p_slave_mode)
        else:
            self.break_timer_stops.emit(p_slave_mode)

