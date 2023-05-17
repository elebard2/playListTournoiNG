from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QGridLayout
from PySide6.QtCore import QTimer

from widgets.editable_label_widget import EditableLabelWidget


def secs_to_hoursminsec(secs: int):
    hours = secs // 3600
    mins = secs // 60
    secs = secs % 60
    if hours > 0:
        hours_mins_secs = f'{hours:02}:{mins:02}:{secs:02}'
    else:
        hours_mins_secs = f'{mins:02}:{secs:02}'
    return hours_mins_secs


class MyTimerWidget(QWidget):
    _timer: QTimer
    _timer_duration: int
    _time_left_int: int
    _title: str
    _title_label: QLabel
    _label_widget: EditableLabelWidget
    _start_pause_button: QPushButton
    _stop_button: QPushButton
    _grid_layout: QGridLayout
    _state_before_edition: dict

    def __init__(self, p_parent, p_timer_duration: int, p_title):
        super().__init__(p_parent)
        self._timer_duration = p_timer_duration
        self._title = p_title
        self.setup_ui()
        self._state_before_edition = {'timer_was_running': False, 'start_button_was_enabled': True,
                                      'stop_button_was_enabled': False}

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layout()
        self.add_widgets_layout()
        self.setup_connections()

    def create_widgets(self):
        # Label Widget
        self._title_label = QLabel(self)
        self._title_label.setText(self._title)

        # Timer and associated editable label
        self._time_left_int = self._timer_duration
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._label_widget = EditableLabelWidget(self)
        hoursminsec = secs_to_hoursminsec(self._time_left_int)
        self._label_widget.setText(hoursminsec)

        # Buttons
        self._start_pause_button = QPushButton(self)
        self._start_pause_button.setText("Start")

        self._stop_button = QPushButton(self)
        self._stop_button.setText("Stop")

    def modify_widgets(self):
        self._stop_button.setEnabled(False)

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
        self._label_widget._label.label_pressed.connect(self.timer_value_under_edition)
        self._label_widget._label.textChanged.connect(self.timer_value_edition_finished)

    def start_timer(self):
        self._stop_button.setEnabled(True)
        self._start_pause_button.setText("Pause")
        self._start_pause_button.clicked.connect(self.pause_timer)
        self._timer.start(1000)

    def pause_timer(self):
        self._timer.stop()
        self._start_pause_button.setText("Start")
        self._start_pause_button.clicked.connect(self.start_timer)

    def stop_timer(self):
        self._timer.stop()
        self._stop_button.setEnabled(False)
        self._start_pause_button.setText("Start")
        self._time_left_int = self._timer_duration
        self.update_gui()

    def timer_timeout(self):
        self._time_left_int -= 1

        if self._time_left_int == 0:
            self._time_left_int = self._timer_duration

        self.update_gui()

    def timer_value_under_edition(self):
        self.save_state()
        self._timer.stop()
        self._start_pause_button.setEnabled(False)
        self._stop_button.setEnabled(False)

    def timer_value_edition_finished(self, p_text_value):
        if self._state_before_edition['timer_was_running']:
            self._timer.start()
        self._start_pause_button.setEnabled(self._state_before_edition['start_button_was_enabled'])
        self._stop_button.setEnabled(self._state_before_edition['stop_button_was_enabled'])

    def update_gui(self):
        minsec = secs_to_hoursminsec(self._time_left_int)
        self._label_widget.setText(minsec)

    def save_state(self):
        self._state_before_edition['timer_was_running'] = self._timer.isActive()
        self._state_before_edition['start_button_was_enabled'] = self._start_pause_button.isEnabled()
        self._state_before_edition['stop_button_was_enabled'] = self._stop_button.isEnabled()
