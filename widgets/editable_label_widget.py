from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import re

MINUTES_ONLY_PATTERN = re.compile(R"^(?P<minutes>\d+)$")
MINUTES_SECONDS_PATTERN = re.compile(R"^(?P<minutes>\d+):(?P<seconds>[0-5]\d)$")
HOURS_MINUTES_SECONDS_PATTERN = re.compile(R"^(?P<hours>\d+):(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d)$")


class KeyPressHandler(QtCore.QObject):
    """Custom key press handler"""
    escapePressed = QtCore.Signal(bool)
    returnPressed = QtCore.Signal(bool)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            event_key = event.key()
            if event_key == QtCore.Qt.Key.Key_Escape:
                self.escapePressed.emit(True)
                return True
            if event_key == QtCore.Qt.Key.Key_Return or event_key == QtCore.Qt.Key.Key_Enter:
                self.returnPressed.emit(True)
                return True

        return QtCore.QObject.eventFilter(self, obj, event)


class EditableLabel(QtWidgets.QWidget):
    """Editable label"""
    textChanged = QtCore.Signal(int)
    label_pressed = QtCore.Signal()
    _label: QtWidgets.QLabel
    _lineEdit: QtWidgets.QLineEdit

    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_editable = True

        self.keyPressHandler = KeyPressHandler(self)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setObjectName("mainLayout")

        self._label = QtWidgets.QLabel(self)
        self._label.setObjectName("label")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        custom_font = QFont()
        custom_font.setPointSize(32)
        self._label.setFont(custom_font)
        self.mainLayout.addWidget(self._label)
        self._lineEdit = QtWidgets.QLineEdit(self)
        self._lineEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lineEdit.setFont(custom_font)
        self._lineEdit.setObjectName("lineEdit")
        regexp = QtCore.QRegularExpression(R"^(\d+:)?(?(1)[0-5]\d|\d+)(?::[0-5]\d)?$")
        validator = QtGui.QRegularExpressionValidator(regexp)
        self._lineEdit.setValidator(validator)
        self.mainLayout.addWidget(self._lineEdit)
        # hide the line edit initially
        self._lineEdit.setHidden(True)

        # setup signals
        self.create_signals()

    def create_signals(self):
        self._lineEdit.installEventFilter(self.keyPressHandler)
        self._label.mousePressEvent = self.label_pressed_event

        # give the lineEdit both a `returnPressed` and `escapedPressed` action
        self.keyPressHandler.escapePressed.connect(self.escape_pressed_action)
        self.keyPressHandler.returnPressed.connect(self.returnPressedAction)

    def text(self):
        """Standard QLabel text getter"""
        return self._label.text()

    def set_text(self, text):
        """Standard QLabel text setter"""
        self._label.blockSignals(True)
        self._label.setText(text)
        self._label.blockSignals(False)

    def label_pressed_event(self, event):
        """Set editable if the left mouse button is clicked"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.label_pressed.emit()
            self.set_label_editable_action()

    def set_label_editable_action(self):
        """Action to make the widget editable"""
        if not self.is_editable:
            return

        self._label.setHidden(True)
        self._label.blockSignals(True)
        self._lineEdit.setHidden(False)
        self._lineEdit.setText(self._label.text())
        self._lineEdit.blockSignals(False)
        self._lineEdit.setFocus(QtCore.Qt.MouseFocusReason)
        self._lineEdit.selectAll()

    def label_updated_action(self):
        """Indicates the widget text has been updated"""
        text_to_update = self._lineEdit.text()

        validator = self._lineEdit.validator()

        validity = validator.validate(text_to_update, 0)
        if validity[0] != QtGui.QValidator.State.Acceptable:
            return

        text_to_update, new_time_value = EditableLabel.fixup_text(text_to_update)

        self._label.setText(text_to_update)
        self.textChanged.emit(new_time_value)

        self._label.setHidden(False)
        self._lineEdit.setHidden(True)
        self._lineEdit.blockSignals(True)
        self._label.blockSignals(False)

    def returnPressedAction(self):
        """Return/enter event handler"""
        self.label_updated_action()

    def escape_pressed_action(self):
        """Escape event handler"""
        self._label.setHidden(False)
        self._lineEdit.setHidden(True)
        self._lineEdit.blockSignals(True)
        self._label.blockSignals(False)

    @staticmethod
    def fixup_text(p_text_to_update):
        m1 = HOURS_MINUTES_SECONDS_PATTERN.match(p_text_to_update)
        m2 = MINUTES_SECONDS_PATTERN.match(p_text_to_update)
        m3 = MINUTES_ONLY_PATTERN.match(p_text_to_update)
        if m1 is not None:
            return p_text_to_update, 3600 * int(m1.group('hours')) + 60 * int(m1.group('minutes')) + int(m1.group('seconds'))
        else:
            is_minutes_only = m3 is not None
            if is_minutes_only:
                seconds_str = "00"
            else:
                seconds_str = f"{m2.group('seconds')}"
            appropriate_matcher = (m2, m3)[is_minutes_only]
            hours_str = ""
            hours = 0
            mins_str = appropriate_matcher.group('minutes')
            mins = int(mins_str)
            if mins > 60:
                hours = mins % 60
                mins = mins - 60 * hours
                hours_str = str(hours)
                mins_str = str(mins)
                if hours < 10:
                    hours_str = "0" + hours_str
                if mins < 10:
                    mins_str = "0" + mins_str
            text = (f"{hours_str}:{mins_str}:{seconds_str}", f"{mins_str}:{seconds_str}")[len(hours_str) == 0]
            return text, 3600 * hours + 60 * mins + int(seconds_str)


class EditableLabelWidget(QtWidgets.QWidget):
    label_pressed = QtCore.Signal()
    text_changed = QtCore.Signal(int)
    _label: EditableLabel
    _layout: QtWidgets.QLayout

    def __init__(self, parent=None):
        super().__init__(parent)

        # create the editable label
        self._label = EditableLabel(self)

        self._layout = QtWidgets.QHBoxLayout()
        self._layout.addWidget(self._label)
        self.setLayout(self._layout)

        self._label.label_pressed.connect(self.emit_label_pressed)
        self._label.textChanged.connect(self.emit_text_changed)

    def set_text(self, p_text):
        self._label.set_text(p_text)

    def emit_label_pressed(self):
        self.label_pressed.emit()

    def emit_text_changed(self, value: int):
        self.text_changed.emit(value)
