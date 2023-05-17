import os.path
import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QStandardPaths, Qt, Slot
from PySide6.QtGui import QIcon, QAction
from PySide6.QtMultimedia import (QAudioOutput, QMediaFormat,
                                  QMediaPlayer)
from PySide6.QtWidgets import (QDialog, QFileDialog,
                               QSlider, QToolBar, QGridLayout, QStatusBar, QLabel)


SONG_TITLE_LABEL_TEXT = "Titre : "
ARTIST_NAME_LABEL_TEXT = "Artiste : "
UNDEFINED_SONG_DURATION = "--:--:--:---"
SEPARATOR = "\\"


def get_supported_mime_types():
    result = []
    for f in QMediaFormat().supportedAudioCodecs(QMediaFormat.ConversionMode.Decode):
        try:
            mime_type = QMediaFormat(QMediaFormat.FileFormat(f)).mimeType()
            result.append(mime_type.name())
        except:
            continue
    return result


class MusicPlayer(QtWidgets.QWidget):
    _layout: QGridLayout
    _audio_output: QAudioOutput
    _player: QMediaPlayer
    _toolbar: QToolBar
    _statusbar: QStatusBar
    _play_action: QAction
    _pause_action: QAction
    _next_action: QAction
    _previous_action: QAction
    _stop_action: QAction
    _volume_slider: QSlider
    _position_slider: QSlider
    _label_song_title: QLabel
    _label_song_title_value: QLabel
    _label_artist_name: QLabel
    _label_artiste_name_value: QLabel
    _label_current_song_position: QLabel
    _label_current_song_duration: QLabel
    _label_separator: QLabel

    def __init__(self, p_parent):
        super().__init__(p_parent)
        self.base_dir = p_parent._base_dir
        self._playlist = []
        self._playlist_index = -1

        self._mime_types = get_supported_mime_types()

        self.setup_ui()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layout()
        self.add_widgets_layout()
        self.setup_connections()

    def create_widgets(self):
        self._audio_output = QAudioOutput()
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio_output)

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

        play_icon = QIcon(os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'play_icon_small.png'))
        self._play_action = self._toolbar.addAction(play_icon, "Play")

        previous_icon = QIcon(
            os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'previous_icon_small.png'))
        self._previous_action = self._toolbar.addAction(previous_icon, "Previous")

        pause_icon = QIcon(os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'pause_icon_small.png'))
        self._pause_action = self._toolbar.addAction(pause_icon, "Pause")

        next_icon = QIcon(os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'next_icon_small.png'))
        self._next_action = self._toolbar.addAction(next_icon, "Next")

        stop_icon = QIcon(os.path.join(self.base_dir, 'resources', 'musicControls', 'V3', 'stop_icon_small.png'))
        self._stop_action = self._toolbar.addAction(stop_icon, "Stop")

        self._volume_slider = QSlider(self)
        self._volume_slider.setOrientation(Qt.Horizontal)
        self._volume_slider.setMinimum(0)
        self._volume_slider.setMaximum(100)
        available_width = self.screen().availableGeometry().width()
        self._volume_slider.setFixedWidth(available_width / 10)
        self._volume_slider.setValue(self._audio_output.volume())
        self._volume_slider.setTickInterval(10)
        self._volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._volume_slider.setToolTip("Volume")
        self._toolbar.addWidget(self._volume_slider)

        self.update_buttons(self._player.playbackState())

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
        self._player.errorOccurred.connect(self._player_error)
        self._player.positionChanged.connect(self.position_changed)
        self._player.durationChanged.connect(self.duration_changed)
        self._play_action.triggered.connect(self._player.play)
        self._previous_action.triggered.connect(self.previous_clicked)
        self._pause_action.triggered.connect(self._player.pause)
        self._next_action.triggered.connect(self.next_clicked)
        self._stop_action.triggered.connect(self._ensure_stopped)
        self._volume_slider.valueChanged.connect(self._audio_output.setVolume)
        self._position_slider.sliderMoved.connect(self.set_position)

    def closeEvent(self, event):
        self._ensure_stopped()
        event.accept()

    @Slot()
    def open(self):
        self._ensure_stopped()
        file_dialog = QFileDialog(self)

        file_dialog.setMimeTypeFilters(self._mime_types)

        movies_location = QStandardPaths.writableLocation(QStandardPaths.MusicLocation)
        file_dialog.setDirectory(movies_location)
        if file_dialog.exec() == QDialog.DialogCode.Accepted:
            url = file_dialog.selectedUrls()[0]
            self._playlist.append(url)

    @Slot()
    def _ensure_stopped(self):
        if self._player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self._player.stop()

    @Slot()
    def previous_clicked(self):
        # Go to previous track if we are within the first 5 seconds of playback
        # Otherwise, seek to the beginning.
        if self._player.position() <= 5000 and self._playlist_index > 0:
            self._playlist_index -= 1
            self._player.setSource(self._playlist[self._playlist_index])
        else:
            self._player.setPosition(0)

    @Slot()
    def next_clicked(self):
        if self._playlist_index < len(self._playlist) - 1:
            self._playlist_index += 1
            self._player.setSource(self._playlist[self._playlist_index])

    @Slot("QMediaPlayer::PlaybackState")
    def update_buttons(self, state):
        media_count = len(self._playlist)
        self._play_action.setEnabled(media_count > 0
                                     and state != QMediaPlayer.PlaybackState.PlayingState)
        self._pause_action.setEnabled(state == QMediaPlayer.PlaybackState.PlayingState)
        self._stop_action.setEnabled(state != QMediaPlayer.PlaybackState.StoppedState)
        self._previous_action.setEnabled(self._player.position() > 0)
        self._next_action.setEnabled(media_count > 1)

    def show_status_message(self, message):
        self._statusbar.showMessage(message, 5000)

    @Slot("QMediaPlayer::Error", str)
    def _player_error(self, error, error_string):
        print(error_string, file=sys.stderr)
        self.show_status_message(error_string)

    def position_changed(self, position):
        self._position_slider.setValue(position)

    def set_position(self, position):
        self._player.setPosition(position)

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
