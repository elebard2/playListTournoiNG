import os.path
import sys
from enum import Enum
from math import sqrt, exp, log
from pathlib import Path

from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QStandardPaths, Qt, Slot, QUrl
from PySide6.QtGui import QIcon, QAction
from PySide6.QtMultimedia import (QAudioOutput, QMediaFormat,
                                  QMediaPlayer)
from PySide6.QtWidgets import (QDialog, QFileDialog,
                               QSlider, QToolBar, QGridLayout, QStatusBar, QLabel)

from api.music.music_object import MusicObject
from config.config import PRELOADED_SOUNDS_DIR_NAME, RESOURCES_DIR_NAME, BUZZER_MATCH_END_FILE_NAME, \
    BUZZER_MATCH_START_FILE_NAME, FIVE_SECONDS_COUNTDOWN_FILE_NAME, ONE_MINUTE_LEFT_FOR_MATCH_FILE_NAME, \
    ONE_MINUTE_LEFT_FOR_BREAK_FILE_NAME

SONG_TITLE_LABEL_TEXT = "Titre : "
ARTIST_NAME_LABEL_TEXT = "Artiste : "
UNDEFINED_SONG_DURATION = "--:--:--"
START_SONG_DURATION = "00:00:00"
SEPARATOR = "\\"


def format_position(position_milliseconds: int):
    if position_milliseconds is not None and isinstance(position_milliseconds, int) and position_milliseconds > 0:
        hours = position_milliseconds // 3600000
        minutes = (position_milliseconds - 3600000 * hours) // 60000
        seconds = (position_milliseconds - 3600000 * hours - 60000 * minutes) // 1000

        if hours == 0:
            str_hours = None
        elif hours < 10:
            str_hours = f"0{hours}"
        else:
            str_hours = f"{hours}"

        if minutes < 10:
            str_minutes = f"0{minutes}"
        else:
            str_minutes = f"{minutes}"

        if seconds < 10:
            str_seconds = f"0{seconds}"
        else:
            str_seconds = f"{seconds}"

        if str_hours is None:
            str_duration = f"{str_minutes}:{str_seconds}"
        else:
            str_duration = f"{str_hours}:{str_minutes}:{str_seconds}"

        return str_duration


def interpret_label_as_position(p_label: str):
    fields = p_label.split(":")
    h = fields[0]
    m = fields[1]
    s = fields[2]
    return 1000 * (3600 * int(h) + 60 * int(m) + int(s))


def get_supported_mime_types():
    result = []
    for f in QMediaFormat().supportedAudioCodecs(QMediaFormat.ConversionMode.Decode):
        try:
            mime_type = QMediaFormat(QMediaFormat.FileFormat(f)).mimeType()
            result.append(mime_type.name())
        except:
            continue
    return result


class MusicPlayerShuffleMode(Enum):
    SHUFFLE_OFF = 1
    SHUFFLE_ON = 2


class MusicPlayerRepeatMode(Enum):
    REPEAT_ALL = 1
    REPEAT_ONE = 2
    NO_REPEAT = 3


class AmbientMusicMode(Enum):
    NO_AMBIENT_MUSIC = 1
    AMBIENT_MUSIC = 2


class MusicPlayer(QtWidgets.QWidget):
    play_button_clicked = QtCore.Signal()
    change_track_button_clicked = QtCore.Signal(int, int, int, int)
    stop_button_pressed = QtCore.Signal()
    request_ambient_music_track = QtCore.Signal()
    music_started_or_resumed = QtCore.Signal()
    music_stopped = QtCore.Signal()

    _current_playlist_index: int
    old_position: int
    _threshold_to_switch: int
    _layout: QGridLayout
    _audio_output_normal_music: QAudioOutput
    _audio_output_ambient_music: QAudioOutput
    _audio_output_events: QAudioOutput
    _normal_music_qmedia_player: QMediaPlayer
    _ambient_music_qmedia_player: QMediaPlayer
    _events_qmedia_player: QMediaPlayer
    _toolbar: QToolBar
    _statusbar: QStatusBar
    _play_action: QAction
    _pause_action: QAction
    _next_action: QAction
    _previous_action: QAction
    _stop_action: QAction
    _switch_shuffle_mode_action: QAction
    _switch_repeat_mode_action: QAction
    _volume_slider: QSlider
    _position_slider: QSlider
    _label_song_title: QLabel
    _label_song_title_value: QLabel
    _label_artist_name: QLabel
    _label_artiste_name_value: QLabel
    _label_current_song_position: QLabel
    _label_current_song_duration: QLabel
    _label_separator: QLabel
    _path_to_start_buzzer_sound: Path
    _path_to_end_buzzer_sound: Path
    _path_to_five_seconds_countdown_sound: Path
    _path_to_one_minute_left_match: Path
    _path_to_one_minute_left_break: Path
    _play_icon: QIcon
    _pause_icon: QIcon
    _stop_icon: QIcon
    _next_icon: QIcon
    _previous_icon: QIcon
    _shuffle_on_icon: QIcon
    _shuffle_off_icon: QIcon
    _repeat_all_icon: QIcon
    _repeat_one_icon: QIcon
    _no_repeat_icon: QIcon
    _shuffle_mode: MusicPlayerShuffleMode
    _repeat_mode: MusicPlayerRepeatMode
    _ambient_music_mode: AmbientMusicMode

    def __init__(self, p_parent):
        super().__init__(p_parent)
        self.old_position = 0
        self._current_playlist_index = -1
        self._threshold_to_switch = -1
        self.base_dir = p_parent._base_dir

        self._mime_types = get_supported_mime_types()

        self._path_to_start_buzzer_sound = self.base_dir / RESOURCES_DIR_NAME / PRELOADED_SOUNDS_DIR_NAME / BUZZER_MATCH_START_FILE_NAME
        self._path_to_end_buzzer_sound = self.base_dir / RESOURCES_DIR_NAME / PRELOADED_SOUNDS_DIR_NAME / BUZZER_MATCH_END_FILE_NAME
        self._path_to_five_seconds_countdown_sound = self.base_dir / RESOURCES_DIR_NAME / PRELOADED_SOUNDS_DIR_NAME / FIVE_SECONDS_COUNTDOWN_FILE_NAME
        self._path_to_one_minute_left_match = self.base_dir / RESOURCES_DIR_NAME / PRELOADED_SOUNDS_DIR_NAME / ONE_MINUTE_LEFT_FOR_MATCH_FILE_NAME
        self._path_to_one_minute_left_break = self.base_dir / RESOURCES_DIR_NAME / PRELOADED_SOUNDS_DIR_NAME / ONE_MINUTE_LEFT_FOR_BREAK_FILE_NAME

        self._shuffle_mode = MusicPlayerShuffleMode.SHUFFLE_OFF
        self._repeat_mode = MusicPlayerRepeatMode.REPEAT_ALL
        self._ambient_music_mode = AmbientMusicMode.NO_AMBIENT_MUSIC

        self.setup_ui()

    @property
    def shuffle_mode(self):
        return self._shuffle_mode

    @shuffle_mode.setter
    def shuffle_mode(self, p_shuffle_mode):
        if isinstance(p_shuffle_mode, MusicPlayerShuffleMode):
            self._shuffle_mode = p_shuffle_mode
        elif isinstance(p_shuffle_mode, int) and (p_shuffle_mode == 1 or p_shuffle_mode == 2 or p_shuffle_mode == 3):
            self._shuffle_mode = MusicPlayerShuffleMode(p_shuffle_mode)

    @property
    def repeat_mode(self):
        return self._repeat_mode

    @repeat_mode.setter
    def repeat_mode(self, p_repeat_mode):
        if isinstance(p_repeat_mode, MusicPlayerRepeatMode):
            self._repeat_mode = p_repeat_mode
        elif isinstance(p_repeat_mode, int) and (p_repeat_mode == 1 or p_repeat_mode == 2):
            self._repeat_mode = MusicPlayerRepeatMode(p_repeat_mode)

    @property
    def ambient_music_mode(self):
        return self._ambient_music_mode

    @ambient_music_mode.setter
    def ambient_music_mode(self, p_ambient_music_mode):
        if isinstance(p_ambient_music_mode, AmbientMusicMode):
            self._ambient_music_mode = p_ambient_music_mode
        elif isinstance(p_ambient_music_mode, int) and (p_ambient_music_mode == 1 or p_ambient_music_mode == 2):
            self._ambient_music_mode = AmbientMusicMode(p_ambient_music_mode)

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layout()
        self.add_widgets_layout()
        self.setup_connections()

    def create_widgets(self):
        self._audio_output_normal_music = QAudioOutput()
        self._audio_output_normal_music.setVolume(0.5)
        self._normal_music_qmedia_player = QMediaPlayer(self)
        self._normal_music_qmedia_player.setAudioOutput(self._audio_output_normal_music)

        self._audio_output_ambient_music = QAudioOutput()
        self._audio_output_ambient_music.setVolume(0.5)
        self._events_qmedia_player = QMediaPlayer(self)
        self._events_qmedia_player.setAudioOutput(self._audio_output_ambient_music)

        self._audio_output_events = QAudioOutput()
        self._audio_output_events.setVolume(0.5)
        self._ambient_music_qmedia_player = QMediaPlayer(self)
        self._ambient_music_qmedia_player.setAudioOutput(self._audio_output_events)

        self._label_song_title = QLabel(self)
        self._label_song_title.setText(SONG_TITLE_LABEL_TEXT)

        self._label_song_title_value = QLabel(self)

        self._label_artist_name = QLabel(self)
        self._label_artist_name.setText(ARTIST_NAME_LABEL_TEXT)

        self._label_artiste_name_value = QLabel(self)

        self._label_current_song_position = QLabel(self)
        self._label_current_song_position.setText(UNDEFINED_SONG_DURATION)

        self._label_separator = QLabel(self)
        self._label_separator.setText(SEPARATOR)

        self._label_current_song_duration = QLabel(self)
        self._label_current_song_duration.setText(UNDEFINED_SONG_DURATION)

        self._position_slider = QSlider(self)
        self._position_slider.setRange(0, 0)
        self._position_slider.setOrientation(Qt.Horizontal)
        self._position_slider.setToolTip("Position")

        self._toolbar = QToolBar(self)

        self._statusbar = QStatusBar(self)

        self._play_icon = QIcon(os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'play_icon_small.png'))
        self._pause_icon = QIcon(
            os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'pause_icon_small.png'))
        self._stop_icon = QIcon(os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'stop_icon_small.png'))
        self._next_icon = QIcon(os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'next_icon_small.png'))
        self._previous_icon = QIcon(
            os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'previous_icon_small.png'))
        self._shuffle_on_icon = QIcon(
            os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'shuffle_on_icon_small.png'))
        self._shuffle_off_icon = QIcon(
            os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'shuffle_off_icon_small.png'))
        self._no_repeat_icon = QIcon(
            os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'no_repeat_icon_small.png'))
        self._repeat_all_icon = QIcon(
            os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'repeat_all_icon_small.png'))
        self._repeat_one_icon = QIcon(
            os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'repeat_one_icon_small.png'))

        self._play_action = self._toolbar.addAction(self._play_icon, "Play")
        self._previous_action = self._toolbar.addAction(self._previous_icon, "Previous")
        self._pause_action = self._toolbar.addAction(self._pause_icon, "Pause")
        self._next_action = self._toolbar.addAction(self._next_icon, "Next")
        self._stop_action = self._toolbar.addAction(self._stop_icon, "Stop")
        self._switch_shuffle_mode_action = self._toolbar.addAction(self._shuffle_off_icon, "Shuffle Mode")
        self._switch_repeat_mode_action = self._toolbar.addAction(self._repeat_all_icon, "Repeat mode")

        self._volume_slider = QSlider(self)
        self._volume_slider.setOrientation(Qt.Horizontal)
        self._volume_slider.setMinimum(0)
        self._volume_slider.setMaximum(100)
        available_width = self.screen().availableGeometry().width()
        self._volume_slider.setFixedWidth(available_width / 10)
        self._volume_slider.setValue(self._audio_output_normal_music.volume())
        self._volume_slider.setTickInterval(10)
        self._volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._volume_slider.setToolTip("Volume")
        self._volume_slider.setSliderPosition(50)
        self._toolbar.addWidget(self._volume_slider)

        self.update_buttons(self._normal_music_qmedia_player.playbackState())

    def modify_widgets(self):
        pass

    def create_layout(self):
        self._layout = QGridLayout(self)

    def add_widgets_layout(self):
        self._layout.addWidget(self._label_artist_name, 0, 0)
        self._layout.addWidget(self._label_artiste_name_value, 0, 2, 1, 2)
        self._layout.addWidget(self._label_song_title, 1, 0)
        self._layout.addWidget(self._label_song_title_value, 1, 2, 1, 2)
        self._layout.addWidget(self._label_current_song_position, 2, 1)
        self._layout.addWidget(self._label_separator, 2, 2)
        self._layout.addWidget(self._label_current_song_duration, 2, 3)
        self._layout.addWidget(self._position_slider, 3, 0, 1, -1)
        self._layout.addWidget(self._toolbar, 4, 0, 1, -1)
        self._layout.addWidget(self._statusbar, 5, 0, 1, -1)

    def setup_connections(self):
        # Connect Normal Music Player Signals
        self._normal_music_qmedia_player.errorOccurred.connect(self.player_error)
        self._normal_music_qmedia_player.positionChanged.connect(self.position_changed)
        self._normal_music_qmedia_player.positionChanged.connect(self._position_slider.setSliderPosition)
        self._normal_music_qmedia_player.durationChanged.connect(self.duration_changed)
        self._normal_music_qmedia_player.sourceChanged.connect(self.source_changed)
        self._normal_music_qmedia_player.playbackStateChanged.connect(self.notify_playback_state_changed)
        self._normal_music_qmedia_player.playbackStateChanged.connect(self.update_buttons)

        # Connect Music Control Actions Signals
        self._play_action.triggered.connect(self.play_clicked)
        self._previous_action.triggered.connect(self.previous_clicked)
        self._pause_action.triggered.connect(self.pause_clicked)
        self._next_action.triggered.connect(self.next_clicked)
        self._stop_action.triggered.connect(self.stop_clicked)
        self._switch_shuffle_mode_action.triggered.connect(self.switch_shuffle_mode_clicked)
        self._switch_repeat_mode_action.triggered.connect(self.switch_repeat_mode_clicked)

        # Connect Sliders Signals
        self._volume_slider.valueChanged.connect(self.set_music_volume_from_volume_slider)
        self._position_slider.sliderMoved.connect(self.handle_music_position_slider_moved)

    def play_clicked(self):
        if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            if self._normal_music_qmedia_player.source() == QUrl(''):
                self.play_button_clicked.emit()
            else:
                self._normal_music_qmedia_player.play()

    def pause_clicked(self):
        if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.PausedState:
            self._normal_music_qmedia_player.pause()

    def stop_clicked(self):
        if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.old_position = 0
            self._label_current_song_position.setText(START_SONG_DURATION)
            self._normal_music_qmedia_player.stop()

    def previous_clicked(self):
        # Go to previous track if we are within the first 5 seconds of playback
        # Otherwise, seek to the beginning.
        if self._normal_music_qmedia_player.position() >= 5000:
            self.change_track_button_clicked.emit(self.repeat_mode.value, self.shuffle_mode.value,
                                                  self._current_playlist_index, -1)
        else:
            self._normal_music_qmedia_player.setPosition(0)

    def next_clicked(self):
        self.change_track_button_clicked.emit(self.repeat_mode.value, self.shuffle_mode.value,
                                              self._current_playlist_index, 1)

    def switch_shuffle_mode_clicked(self):
        if self.shuffle_mode == MusicPlayerShuffleMode.SHUFFLE_ON:
            self.shuffle_mode = MusicPlayerShuffleMode.SHUFFLE_OFF
            self._switch_shuffle_mode_action.setIcon(self._shuffle_off_icon)
        else:
            self.shuffle_mode = MusicPlayerShuffleMode.SHUFFLE_ON
            self._switch_shuffle_mode_action.setIcon(self._shuffle_on_icon)

    def switch_repeat_mode_clicked(self):
        if self.repeat_mode == MusicPlayerRepeatMode.REPEAT_ALL:
            self.repeat_mode = MusicPlayerRepeatMode.REPEAT_ONE
            self._switch_repeat_mode_action.setIcon(self._repeat_one_icon)
        elif self.repeat_mode == MusicPlayerRepeatMode.REPEAT_ONE:
            self.repeat_mode = MusicPlayerRepeatMode.NO_REPEAT
            self._switch_repeat_mode_action.setIcon(self._no_repeat_icon)
        else:
            self.repeat_mode = MusicPlayerRepeatMode.REPEAT_ALL
            self._switch_repeat_mode_action.setIcon(self._repeat_all_icon)

    def update_buttons(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self._play_action.setEnabled(True)
            self._stop_action.setEnabled(False)
            self._pause_action.setEnabled(False)
            self._next_action.setEnabled(False)
            self._previous_action.setEnabled(False)
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self._play_action.setEnabled(True)
            self._stop_action.setEnabled(True)
            self._pause_action.setEnabled(False)
            self._next_action.setEnabled(True)
            self._previous_action.setEnabled(True)
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_action.setEnabled(False)
            self._stop_action.setEnabled(True)
            self._pause_action.setEnabled(True)
            self._next_action.setEnabled(True)
            self._previous_action.setEnabled(True)

    def source_changed(self, p_url: QUrl):
        music_object = MusicObject(Path(p_url.toLocalFile()))
        self._label_song_title_value.setText(music_object.title)
        self._label_artiste_name_value.setText(music_object.artist)
        self._threshold_to_switch = music_object.duration * 1000 - 100
        self._label_current_song_duration.setText(music_object.format_duration())
        self._label_current_song_position.setText(START_SONG_DURATION)
        self.old_position = 0

    def position_changed(self, position):
        delta = position - self.old_position
        if delta >= 1000:
            self._label_current_song_position.setText(format_position(position))
            self.old_position = position
        if position >= self._threshold_to_switch:
            self.next_clicked()

    def handle_music_position_slider_moved(self, position):
        self._normal_music_qmedia_player.setPosition(position)
        self._label_current_song_position.setText(format_position(position))

    def duration_changed(self, duration):
        self._position_slider.setRange(0, duration)

    @Slot("QMediaPlayer::Error", str)
    def player_error(self, error: QMediaPlayer.Error, error_string):
        print(self._normal_music_qmedia_player.source())
        print(error)
        print(error_string, file=sys.stderr)

    def enable_all_music_player_actions(self):
        state = self._normal_music_qmedia_player.playbackState()
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self._play_action.setEnabled(True)
            self._stop_action.setEnabled(False)
            self._pause_action.setEnabled(False)
            self._next_action.setEnabled(False)
            self._previous_action.setEnabled(False)
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self._play_action.setEnabled(True)
            self._stop_action.setEnabled(True)
            self._pause_action.setEnabled(False)
            self._next_action.setEnabled(True)
            self._previous_action.setEnabled(True)
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_action.setEnabled(False)
            self._stop_action.setEnabled(True)
            self._pause_action.setEnabled(True)
            self._next_action.setEnabled(True)
            self._previous_action.setEnabled(True)

    def disable_all_music_player_actions(self):
        self._play_action.setEnabled(False)
        self._pause_action.setEnabled(False)
        self._stop_action.setEnabled(False)
        self._next_action.setEnabled(False)
        self._previous_action.setEnabled(False)
        self._switch_repeat_mode_action.setEnabled(False)
        self._switch_shuffle_mode_action.setEnabled(False)

    def handle_timer_starts(self, p_timer_id: int):
        if p_timer_id == 1:
            self.enable_all_music_player_actions()
            if self._ambient_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self._ambient_music_qmedia_player.stop()
            if self._events_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self._events_qmedia_player.stop()
            self._events_qmedia_player.setSource(QUrl(''))
            self._events_qmedia_player.setSource(QUrl.fromLocalFile(str(self._path_to_start_buzzer_sound)))
            self._events_qmedia_player.play()
        elif self.ambient_music_mode == AmbientMusicMode.AMBIENT_MUSIC:
            if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self._normal_music_qmedia_player.stop()
            if self._ambient_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self.request_ambient_music_track.emit()

    def handle_break_timer_threshold(self, p_threshold: int):
        if self._events_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._events_qmedia_player.stop()
        if p_threshold == 60:
            self._events_qmedia_player.setSource(QUrl.fromLocalFile(str(self._path_to_one_minute_left_break)))
        elif p_threshold == 5:
            self._events_qmedia_player.setSource(QUrl.fromLocalFile(str(self._path_to_five_seconds_countdown_sound)))
        self._events_qmedia_player.play()

    def handle_match_timer_threshold(self, p_threshold: int):
        if self._events_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._events_qmedia_player.stop()
        if p_threshold == 60:
            self._events_qmedia_player.setSource(QUrl.fromLocalFile(str(self._path_to_one_minute_left_match)))
        elif p_threshold == 5:
            self._events_qmedia_player.setSource(QUrl.fromLocalFile(str(self._path_to_five_seconds_countdown_sound)))
        self._events_qmedia_player.play()

    def handle_match_timer_ends(self):
        if self.ambient_music_mode.value == 2:
            if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self._normal_music_qmedia_player.stop()
            if self._events_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self._events_qmedia_player.stop()
            self.disable_all_music_player_actions()
            self._events_qmedia_player.setSource(QUrl.fromLocalFile(str(self._path_to_end_buzzer_sound)))
            self._events_qmedia_player.play()
            if self._ambient_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self.request_ambient_music_track.emit()

    def handle_match_timer_stops(self):
        pass

    def handle_break_timer_ends(self, p_mode: int):
        if p_mode == 2:
            if self._ambient_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self._ambient_music_qmedia_player.stop()
            if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self._normal_music_qmedia_player.play()
            self.enable_all_music_player_actions()

    def handle_break_timer_stops(self):
        pass

    def handle_music_to_play_received(self, p_music_file_path: str, p_playlist_index: int):
        if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._normal_music_qmedia_player.stop()
        self._current_playlist_index = p_playlist_index
        self._normal_music_qmedia_player.setSource(QUrl.fromLocalFile(p_music_file_path))
        self._normal_music_qmedia_player.setLoops(1)
        self._normal_music_qmedia_player.play()

    def handle_receive_ambient_music(self, p_ambient_music_file_path: str):
        if p_ambient_music_file_path is not None and Path(p_ambient_music_file_path).exists:
            if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self._normal_music_qmedia_player.stop()
            if self._ambient_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self._ambient_music_qmedia_player.stop()
            self._ambient_music_qmedia_player.setSource(QUrl.fromLocalFile(p_ambient_music_file_path))
            self._ambient_music_qmedia_player.setLoops(QMediaPlayer.Loops.Infinite)
            self._ambient_music_qmedia_player.play()

    def toggle_mode(self, state):
        if state == 2:
            self.ambient_music_mode = 2
        elif state == 0:
            self.ambient_music_mode = 1

    def handle_received_song_to_play(self, p_path_to_music: str, p_position_in_playlist: int):
        if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._normal_music_qmedia_player.stop()
        self._normal_music_qmedia_player.setSource(QUrl.fromLocalFile(p_path_to_music))
        self._current_playlist_index = p_position_in_playlist

    def notify_playback_state_changed(self, p_state: QMediaPlayer.PlaybackState):
        if p_state == QMediaPlayer.PlaybackState.PlayingState:
            self.music_started_or_resumed.emit()
        elif p_state == QMediaPlayer.PlaybackState.StoppedState:
            self.music_stopped.emit()

    def handle_playlist_switched(self):
        if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._normal_music_qmedia_player.stop()
        self._current_playlist_index = 0
        self.change_track_button_clicked.emit(self.repeat_mode.value, self.shuffle_mode.value,
                                              self._current_playlist_index, -1)
        self.enable_all_music_player_actions()

    def handle_no_more_playlist(self):
        if self._normal_music_qmedia_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._normal_music_qmedia_player.stop()
        self._normal_music_qmedia_player.setSource(QUrl())
        self.disable_all_music_player_actions()

    def set_music_volume_from_volume_slider(self, p_position: int):
        self._audio_output_normal_music.setVolume(exp(log(1000) * p_position / 100)/250)
