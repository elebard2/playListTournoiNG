import sys, os

from PySide6 import QtWidgets

from widgets.main_window import MainWindow

basedir = os.path.dirname(__file__)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    widget = MainWindow(basedir)
    widget.showMaximized()
    widget.show()

    sys.exit(app.exec())


