from enum import Enum

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QGridLayout
from PySide6.QtCore import QTimer

from widgets.editable_label_widget import EditableLabelWidget

START_BUTTON_TEXT = "Démarrer"
PAUSE_BUTTON_TEXT = "Pause"
RESUME_BUTTON_TEXT = "Reprendre"
STOP_BUTTON_TEXT = "Arrêter"


def secs_to_hoursminsec(secs: int):
    hours = secs // 3600
    mins = (secs - 3600 * hours) // 60
    secs = secs % 60
    if hours > 0:
        hours_mins_secs = f'{hours:02}:{mins:02}:{secs:02}'
    else:
        hours_mins_secs = f'{mins:02}:{secs:02}'
    return hours_mins_secs


class TimerMode(Enum):
    FREE = 1
    SLAVE = 2


class TimerIdentifier(Enum):
    MATCH = 1
    BREAK = 2


class TimerState:
    _timer_was_running: bool
    _start_button_was_enabled: bool
    _stop_button_was_enabled: bool

    def __init__(self):
        self._timer_was_running = False
        self._start_button_was_enabled = True
        self._stop_button_was_enabled = False

    @property
    def running(self):
        return self._timer_was_running

    @running.setter
    def running(self, p_running):
        if isinstance(p_running, bool):
            self._timer_was_running = p_running

    @property
    def start_enabled(self):
        return self._start_button_was_enabled

    @start_enabled.setter
    def start_enabled(self, p_start_enabled):
        if isinstance(p_start_enabled, bool):
            self._start_button_was_enabled = p_start_enabled

    @property
    def stop_enabled(self):
        return self._stop_button_was_enabled

    @stop_enabled.setter
    def stop_enabled(self, p_stop_enabled):
        if isinstance(p_stop_enabled, bool):
            self._stop_button_was_enabled = p_stop_enabled


class MyTimerWidget(QWidget):
    timer_starts = QtCore.Signal(int)
    timer_ends = QtCore.Signal(int)
    timer_specific_threshold = QtCore.Signal(int)
    timer_stops = QtCore.Signal(int, int)

    _timer: QTimer
    _timer_duration: int
    _time_left: int
    _identifier: TimerIdentifier
    _title_label: QLabel
    _label_widget: EditableLabelWidget
    _start_pause_button: QPushButton
    _stop_button: QPushButton
    _grid_layout: QGridLayout
    _state_before_edition: TimerState
    _mode: TimerMode

    def __init__(self, p_parent, p_timer_duration: int, p_identifier: int):
        super().__init__(p_parent)
        self.timer_duration = p_timer_duration
        self.time_left = self.timer_duration
        self.identifier = p_identifier
        self.mode = TimerMode.FREE if self.identifier == TimerIdentifier.MATCH else TimerMode.SLAVE
        self.setup_ui()
        self._state_before_edition = TimerState()

    def setup_ui(self):
        self.create_widgets()
        self.create_layout()
        self.add_widgets_layout()
        self.setup_connections()
        self.modify_widgets()

    def create_widgets(self):
        # Label Widget
        self._title_label = QLabel(self)
        self._title_label.setText(self.identifier.name)

        # Timer and associated editable label
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._label_widget = EditableLabelWidget(self)
        hours_mins_secs = secs_to_hoursminsec(self._time_left)
        self._label_widget.set_text(hours_mins_secs)

        # Buttons
        self._start_pause_button = QPushButton(self)
        self._start_pause_button.setText(START_BUTTON_TEXT)

        self._stop_button = QPushButton(self)
        self._stop_button.setText(STOP_BUTTON_TEXT)

    def modify_widgets(self):
        self._stop_button.setEnabled(False)
        if self.identifier == TimerIdentifier.BREAK:
            self._start_pause_button.setEnabled(False)
            self._start_pause_button.setText(PAUSE_BUTTON_TEXT)
            self._start_pause_button.clicked.connect(self.pause_timer)
            self._stop_button.setVisible(False)

    def create_layout(self):
        self._grid_layout = QGridLayout(self)

    def add_widgets_layout(self):
        self._grid_layout.addWidget(self._title_label, 0, 0, 1, -1)
        self._grid_layout.addWidget(self._label_widget, 1, 0, 1, -1)
        self._grid_layout.addWidget(self._start_pause_button, 2, 0)
        self._grid_layout.addWidget(self._stop_button, 2, 1)

    def setup_connections(self):
        self._start_pause_button.clicked.connect(self.start_timer)
        self._stop_button.clicked.connect(self.stop_timer)
        self._timer.timeout.connect(self.timer_timeout)
        self._label_widget.label_pressed.connect(self.timer_value_under_edition)
        self._label_widget.text_changed.connect(self.timer_value_edition_finished)

    def start_timer(self):
        self._stop_button.setEnabled(True)
        self._start_pause_button.setEnabled(True)
        self._start_pause_button.setText("Pause")
        self._start_pause_button.clicked.disconnect(self.start_timer)
        self._start_pause_button.clicked.connect(self.pause_timer)
        self._timer.start(1000)
        self.timer_starts.emit(self.identifier.value)

    def pause_timer(self):
        self._timer.stop()
        self._start_pause_button.setText(RESUME_BUTTON_TEXT)
        self._start_pause_button.clicked.disconnect(self.pause_timer)
        self._start_pause_button.clicked.connect(self.start_timer)

    def stop_timer(self):
        self._timer.stop()
        self._stop_button.setEnabled(False)
        self._start_pause_button.setText(START_BUTTON_TEXT)
        self._start_pause_button.clicked.connect(self.start_timer)
        self.time_left = self.timer_duration
        self.update_gui()
        if self.mode == TimerMode.SLAVE:
            self._start_pause_button.setEnabled(False)
            self._start_pause_button.setText(PAUSE_BUTTON_TEXT)
            self._start_pause_button.clicked.connect(self.pause_timer)
        self.timer_stops.emit(self.identifier.value, self.mode.value)

    def timer_timeout(self):
        self.time_left -= 1

        if self.time_left == 60 or self.time_left == 5:
            self.timer_specific_threshold.emit(self.time_left)

        if self.time_left == 0:
            self.time_left = self.timer_duration
            self.stop_timer()
            self.timer_ends.emit(self.identifier.value)

        self.update_gui()

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, p_identifier):
        if isinstance(p_identifier, str):
            if p_identifier.upper() == "BREAK":
                self._identifier = TimerIdentifier.BREAK
            elif p_identifier.upper() == "MATCH":
                self._identifier = TimerIdentifier.MATCH
        elif (isinstance(p_identifier, int) and p_identifier == 1 or p_identifier == 2) or isinstance(p_identifier,
                                                                                                      TimerIdentifier):
            self._identifier = TimerIdentifier(p_identifier)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, p_mode):
        if isinstance(p_mode, str):
            if p_mode.upper() == "FREE":
                self._mode = TimerMode.FREE
            elif p_mode.upper() == "SLAVE":
                self._mode = TimerMode.SLAVE
        elif (isinstance(p_mode, int) and p_mode == 1 or p_mode == 2) or isinstance(p_mode,
                                                                                    TimerMode):
            self._mode = TimerMode(p_mode)

    @property
    def timer_duration(self):
        return self._timer_duration

    @timer_duration.setter
    def timer_duration(self, p_timer_duration):
        if isinstance(p_timer_duration, int):
            self._timer_duration = p_timer_duration

    @property
    def time_left(self):
        return self._time_left

    @time_left.setter
    def time_left(self, p_time_left):
        if isinstance(p_time_left, int):
            self._time_left = p_time_left

    def timer_value_under_edition(self):
        self.save_state()
        self._timer.stop()
        self._start_pause_button.setEnabled(False)
        self._stop_button.setEnabled(False)

    def timer_value_edition_finished(self, p_new_time_left):
        previous_time_left = self.time_left
        self.time_left = p_new_time_left
        self.timer_duration += self.time_left - previous_time_left
        if self._state_before_edition.running:
            self._timer.start()
        self._start_pause_button.setEnabled(self._state_before_edition.start_enabled)
        self._stop_button.setEnabled(self._state_before_edition.stop_enabled)

    def update_gui(self):
        minsec = secs_to_hoursminsec(self._time_left)
        self._label_widget.set_text(minsec)

    def save_state(self):
        self._state_before_edition.running = self._timer.isActive()
        self._state_before_edition.start_enabled = self._start_pause_button.isEnabled()
        self._state_before_edition.stop_enabled = self._stop_button.isEnabled()

    def switch_mode(self, mode):
        if mode == 2:
            self.mode = TimerMode.SLAVE
            self._start_pause_button.setEnabled(False)
            self._start_pause_button.setText(PAUSE_BUTTON_TEXT)
            self._stop_button.setVisible(False)
            self._start_pause_button.clicked.connect(self.pause_timer)
        else:
            self.mode = TimerMode.FREE
            self._start_pause_button.setEnabled(True)
            self._start_pause_button.setText(START_BUTTON_TEXT)
            self._stop_button.setVisible(True)
            self._start_pause_button.clicked.connect(self.start_timer)
