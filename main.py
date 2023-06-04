import os
import sys
from pathlib import Path

from PySide6 import QtWidgets

from widgets.main_window import MainWindow
from config.config import USER_DATA_FOLDER, MUSICS_AND_PLAYLISTS_DIR_NAME
from api.music.music_and_playlists_manager import MusicAndPlaylistsManager

basedir = Path(os.path.dirname(__file__))


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    user_data_dir = basedir / USER_DATA_FOLDER
    music_and_playlists_dir = user_data_dir / MUSICS_AND_PLAYLISTS_DIR_NAME

    if not user_data_dir.exists():
        user_data_dir.mkdir()

    if not music_and_playlists_dir.exists():
        music_and_playlists_dir.mkdir()

    musics_and_playlists_manager = MusicAndPlaylistsManager()
    musics_and_playlists_manager.start(user_data_dir)

    widget = MainWindow(basedir)
    widget.showMaximized()
    widget.show()

    sys.exit(app.exec())


