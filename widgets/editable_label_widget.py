from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import re

SINGLE_DIGIT_PATTERN = re.compile(R"\d")
MULTI_DIGITS_PATTERN = re.compile(R"\d{2,}")
SINGLE_DIGIT_WITH_SECONDS_PATTERN = re.compile(R"\d:[0-5]\d")
MULTI_DIGITS_WITH_SECONDS_PATTERN = re.compile(R"\d{2,}:[0-5]\d")

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
    textChanged = QtCore.Signal(str)
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
        regexp = QtCore.QRegularExpression(R"^(\d{1,2}:)?(?(1)[0-5]\d|\d+)(?::[0-5]\d)?$")
        validator = QtGui.QRegularExpressionValidator(regexp)
        self._lineEdit.setValidator(validator)
        self.mainLayout.addWidget(self._lineEdit)
        # hide the line edit initially
        self._lineEdit.setHidden(True)

        # setup signals
        self.create_signals()

    # def setup_ui(self):
    #     self.create_widgets()
    #     self.modify_widgets()
    #     self.create_layout()
    #     self.add_widgets_layout()
    #     self.setup_connections()
    #
    # def create_widgets(self):
    #     pass
    #
    # def modify_widgets(self):
    #     pass
    #
    # def create_layout(self):
    #     pass
    #
    # def add_widgets_layout(self):
    #     pass
    #
    # def setup_connections(self):
    #     pass

    def create_signals(self):
        self._lineEdit.installEventFilter(self.keyPressHandler)
        self._label.mousePressEvent = self.labelPressedEvent

        # give the lineEdit both a `returnPressed` and `escapedPressed` action
        self.keyPressHandler.escapePressed.connect(self.escapePressedAction)
        self.keyPressHandler.returnPressed.connect(self.returnPressedAction)

    def text(self):
        """Standard QLabel text getter"""
        return self._label.text()

    def setText(self, text):
        """Standard QLabel text setter"""
        self._label.blockSignals(True)
        self._label.setText(text)
        self._label.blockSignals(False)

    def labelPressedEvent(self, event):
        """Set editable if the left mouse button is clicked"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.label_pressed.emit()
            self.setLabelEditableAction()

    def setLabelEditableAction(self):
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

    def labelUpdatedAction(self):
        """Indicates the widget text has been updated"""
        text_to_update = self._lineEdit.text()

        validator = self._lineEdit.validator()

        validity = validator.validate(text_to_update, 0)
        if validity[0] != QtGui.QValidator.State.Acceptable:
            return

        text_to_update = self.fixup_text(text_to_update)

        self._label.setText(text_to_update)
        self.textChanged.emit(text_to_update)

        self._label.setHidden(False)
        self._lineEdit.setHidden(True)
        self._lineEdit.blockSignals(True)
        self._label.blockSignals(False)

    def returnPressedAction(self):
        """Return/enter event handler"""
        self.labelUpdatedAction()

    def escapePressedAction(self):
        """Escape event handler"""
        self._label.setHidden(False)
        self._lineEdit.setHidden(True)
        self._lineEdit.blockSignals(True)
        self._label.blockSignals(False)

    def fixup_text(self, p_text_to_update):
        text_to_update = p_text_to_update
        if MULTI_DIGITS_WITH_SECONDS_PATTERN.match(p_text_to_update) is not None:
            text_to_update = p_text_to_update
        elif SINGLE_DIGIT_WITH_SECONDS_PATTERN.match(p_text_to_update) is not None:
            text_to_update = "0" + p_text_to_update
        elif MULTI_DIGITS_PATTERN.match(p_text_to_update):
            text_to_update = p_text_to_update + ":00"
        elif SINGLE_DIGIT_PATTERN.match(p_text_to_update) is not None:
            text_to_update = "0" + p_text_to_update + ":00"
        return text_to_update


class EditableLabelWidget(QtWidgets.QWidget):
    """Sample Widget"""

    _label: EditableLabel
    _layout: QtWidgets.QLayout

    def __init__(self, parent=None):
        super().__init__(parent)

        # create the editable label
        self._label = EditableLabel(self)

        self._layout = QtWidgets.QHBoxLayout()
        self._layout.addWidget(self._label)
        self.setLayout(self._layout)

    def setText(self, p_text):
        self._label.setText(p_text)
