import os

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QBoxLayout

from widgets.main_widget import MainWidget


class MainWindow(QtWidgets.QMainWindow):
    _base_dir: str
    main_widget: MainWidget
    layout: QBoxLayout

    def __init__(self, p_base_dir):
        super().__init__()
        self._base_dir = p_base_dir
        self.setWindowTitle("Music Player - Volleyball NG")
        self.setWindowIcon(
            QtGui.QIcon(os.path.join(self._base_dir, 'resources', 'appIcon', 'beach_volley_icon.ico')))
        QtGui.QImage(os.path.join(self._base_dir, 'resources', 'background', 'beach_volley_match_affiche.png'))
        self.setObjectName("MainWindow")
        self.setup_ui()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layout()
        self.add_widgets_layout()
        self.setup_connections()

    def create_widgets(self):
        self.main_widget = MainWidget(self)

    def modify_widgets(self):
        pass

    def create_layout(self):
        self.setCentralWidget(self.main_widget)

    def add_widgets_layout(self):
        pass

    def setup_connections(self):
        pass
