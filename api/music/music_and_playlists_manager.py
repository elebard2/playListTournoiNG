import uuid
import inspect
from pathlib import Path
import sqlite3
from sqlite3 import Error
import shutil
from typing import List

from api.music.music_object import MusicObject
from api.music.playlist import Playlist
from api.util.singleton import Singleton
from config.config import MUSICS_AND_PLAYLISTS_DIR_NAME, MUSICS_ARCHIVE_DIR_NAME, AMBIENT_MUSICS_ARCHIVE_DIR_NAME, \
    DATABASE_MUSICS_FILE_NAME, RESOURCES_DIR_NAME, PRELOADED_SOUNDS_DIR_NAME, AMBIENT_RAIN_FILE_NAME, \
    AMBIENT_SHREKSOPHONE_FILE_NAME

SQL_SONGS_TABLE_NAME = "songs"
SQL_PLAYLISTS_TABLE_NAME = "playlists"
SQL_PLAYLIST_SONGS_TABLE_NAME = "playlist_songs"
SQL_AMBIENT_MUSICS_TABLE_NAME = "ambient_musics"

SQL_ID_COLUMN_NAME = "id"
SQL_NAME_COLUMN_NAME = "name"
SQL_TITLE_COLUMN_NAME = "title"
SQL_ARTIST_COLUMN_NAME = "artist"
SQL_DURATION_COLUMN_NAME = "duration"
SQL_FILE_PATH_COLUMN_NAME = "file_path"
SQL_PLAYLIST_ID_COLUMN_NAME = "playlist_id"
SQL_SONG_ID_COLUMN_NAME = "song_id"
SQL_PLAYLIST_POSITION_COLUMN_NAME = "playlist_position"
SQL_SELECTED_COLUMN_NAME = "selected"
SQL_CREATION_TIME_STAMP_COLUMN_NAME = "creation_time_stamp"

ACCEPTED_MUSIC_EXTENSIONS = [".mp3", ".ogg", ".flac"]

# CREATE TABLE requests
sql_create_playlists_table = f""" CREATE TABLE IF NOT EXISTS {SQL_PLAYLISTS_TABLE_NAME} (
                                        {SQL_ID_COLUMN_NAME} TEXT PRIMARY KEY,
                                        {SQL_NAME_COLUMN_NAME} TEXT NOT NULL,
                                        {SQL_CREATION_TIME_STAMP_COLUMN_NAME} REAL NOT NULL
                                    ); """

sql_create_songs_table = f"""CREATE TABLE IF NOT EXISTS {SQL_SONGS_TABLE_NAME} (
                                    {SQL_ID_COLUMN_NAME} TEXT PRIMARY KEY,
                                    {SQL_TITLE_COLUMN_NAME} TEXT NOT NULL,
                                    {SQL_ARTIST_COLUMN_NAME} TEXT NOT NULL,
                                    {SQL_DURATION_COLUMN_NAME} REAL NOT NULL,
                                    {SQL_FILE_PATH_COLUMN_NAME} TEXT NOT NULL,
                                    UNIQUE({SQL_FILE_PATH_COLUMN_NAME})
                                );"""

sql_create_playlists_songs_table = f"""CREATE TABLE IF NOT EXISTS {SQL_PLAYLIST_SONGS_TABLE_NAME} (
                                        {SQL_ID_COLUMN_NAME} integer PRIMARY KEY,
                                        {SQL_PLAYLIST_ID_COLUMN_NAME} TEXT,
                                        {SQL_SONG_ID_COLUMN_NAME} TEXT,
                                        {SQL_PLAYLIST_POSITION_COLUMN_NAME} INTEGER NOT NULL,
                                        FOREIGN KEY ({SQL_PLAYLIST_ID_COLUMN_NAME}) REFERENCES {SQL_PLAYLISTS_TABLE_NAME} ({SQL_ID_COLUMN_NAME}),
                                        FOREIGN KEY ({SQL_SONG_ID_COLUMN_NAME}) REFERENCES {SQL_SONGS_TABLE_NAME} ({SQL_ID_COLUMN_NAME}),
                                        UNIQUE({SQL_PLAYLIST_ID_COLUMN_NAME}, {SQL_SONG_ID_COLUMN_NAME}, {SQL_PLAYLIST_POSITION_COLUMN_NAME})
                                    );"""

sql_create_break_musics_table = f"""CREATE TABLE IF NOT EXISTS {SQL_AMBIENT_MUSICS_TABLE_NAME} (
                                    {SQL_ID_COLUMN_NAME} TEXT PRIMARY KEY,
                                    {SQL_TITLE_COLUMN_NAME} TEXT NOT NULL,
                                    {SQL_ARTIST_COLUMN_NAME} TEXT NOT NULL,
                                    {SQL_DURATION_COLUMN_NAME} REAL NOT NULL,
                                    {SQL_FILE_PATH_COLUMN_NAME} TEXT NOT NULL,
                                    {SQL_SELECTED_COLUMN_NAME} INTEGER NOT NULL,
                                    UNIQUE({SQL_FILE_PATH_COLUMN_NAME})
                                );"""

# INSERT Requests
sql_insert_one_song = f"""INSERT OR IGNORE INTO {SQL_SONGS_TABLE_NAME}({SQL_ID_COLUMN_NAME},{SQL_TITLE_COLUMN_NAME},{SQL_ARTIST_COLUMN_NAME},{SQL_DURATION_COLUMN_NAME},{SQL_FILE_PATH_COLUMN_NAME})
                        VALUES(?,?,?,?,?) """

sql_insert_one_ambient_music = f"""INSERT OR IGNORE INTO {SQL_AMBIENT_MUSICS_TABLE_NAME}({SQL_ID_COLUMN_NAME},{SQL_TITLE_COLUMN_NAME},{SQL_ARTIST_COLUMN_NAME},{SQL_DURATION_COLUMN_NAME},{SQL_FILE_PATH_COLUMN_NAME},{SQL_SELECTED_COLUMN_NAME})
                        VALUES(?,?,?,?,?,?) """

sql_insert_one_playlist = f"""INSERT OR IGNORE INTO {SQL_PLAYLISTS_TABLE_NAME}({SQL_ID_COLUMN_NAME},{SQL_NAME_COLUMN_NAME},{SQL_CREATION_TIME_STAMP_COLUMN_NAME})
                            VALUES(?,?,?) """

sql_insert_one_playlist_song_entry = f"""INSERT OR IGNORE INTO playlist_songs({SQL_PLAYLIST_ID_COLUMN_NAME},{SQL_SONG_ID_COLUMN_NAME},{SQL_PLAYLIST_POSITION_COLUMN_NAME})
                                    VALUES(?,?,?) """

# SELECT Requests
sql_select_all_songs = f"SELECT * FROM {SQL_SONGS_TABLE_NAME}"

sql_select_a_song_by_id = f"SELECT * FROM {SQL_SONGS_TABLE_NAME} WHERE {SQL_ID_COLUMN_NAME}=?"

sql_select_all_playlists = f"SELECT * FROM {SQL_PLAYLISTS_TABLE_NAME}"

sql_select_one_playlist_by_id = f"SELECT * FROM {SQL_PLAYLISTS_TABLE_NAME} WHERE {SQL_ID_COLUMN_NAME}=?"

sql_select_all_songs_for_playlist = f"""SELECT 
                                 {SQL_SONG_ID_COLUMN_NAME}
                                 FROM {SQL_PLAYLIST_SONGS_TABLE_NAME}
                                 WHERE {SQL_PLAYLIST_ID_COLUMN_NAME}=?
                                 ORDER BY {SQL_PLAYLIST_POSITION_COLUMN_NAME}"""

sql_select_all_ambient_musics = f"SELECT * FROM {SQL_AMBIENT_MUSICS_TABLE_NAME}"

sql_select_an_ambient_music_by_id = f"SELECT * FROM {SQL_AMBIENT_MUSICS_TABLE_NAME} WHERE {SQL_ID_COLUMN_NAME}=?"

# DELETE Requests
sql_delete_one_song = f"""DELETE FROM {SQL_SONGS_TABLE_NAME} WHERE {SQL_ID_COLUMN_NAME}=?"""

sql_delete_all_songs = f"""DELETE FROM {SQL_SONGS_TABLE_NAME}"""

sql_delete_one_playlist = f"""DELETE FROM {SQL_PLAYLISTS_TABLE_NAME} WHERE {SQL_ID_COLUMN_NAME}=?"""

sql_delete_all_ps_entries = f"DELETE FROM {SQL_PLAYLIST_SONGS_TABLE_NAME}"

sql_delete_ps_entries_for_playlist = f"DELETE FROM {SQL_PLAYLIST_SONGS_TABLE_NAME} WHERE {SQL_PLAYLIST_ID_COLUMN_NAME}=?"

sql_delete_ps_entries_for_song = f"DELETE FROM {SQL_PLAYLIST_SONGS_TABLE_NAME} WHERE {SQL_SONG_ID_COLUMN_NAME}=?"


class MusicAndPlaylistsManager(Singleton):
    _base_dir: Path
    _stored_songs: dict
    _stored_playlists: dict
    _stored_ambient_musics: dict
    _selected_ambient_music: uuid.UUID

    # Start
    def start(self, p_base_dir):
        self._stored_songs = {}
        self._stored_playlists = {}
        self._stored_ambient_musics = {}
        self._selected_ambient_music = uuid.UUID(int=0)
        self.set_base_dir(p_base_dir)
        self.mkdirs()
        self.init_db()
        self.load_all_available_ambient_music_in_memory()
        self.load_all_available_songs_in_memory()
        self.load_all_available_playlists_in_memory()

    def stop(self):
        music_objects_to_keep = self.save_all()
        self.clean_music_archive(music_objects_to_keep)

    # Files Management
    def set_base_dir(self, p_base_dir):
        self._base_dir = p_base_dir / MUSICS_AND_PLAYLISTS_DIR_NAME

    def mkdirs(self):
        music_archives_folder_path = self.get_musics_archive_folder()
        if not music_archives_folder_path.exists():
            music_archives_folder_path.mkdir(parents=True)
        ambient_music_folder_path = self.get_ambient_musics_archive_folder()
        if not ambient_music_folder_path.exists():
            ambient_music_folder_path.mkdir(parents=True)

    def get_db_file_path(self):
        return self._base_dir / DATABASE_MUSICS_FILE_NAME

    def get_musics_archive_folder(self):
        return self._base_dir / MUSICS_ARCHIVE_DIR_NAME

    def get_ambient_musics_archive_folder(self):
        return self._base_dir / AMBIENT_MUSICS_ARCHIVE_DIR_NAME

    def get_preloaded_sounds_folder(self):
        return self._base_dir.parent.parent / RESOURCES_DIR_NAME / PRELOADED_SOUNDS_DIR_NAME

    def get_all_music_files_in_archive(self):
        music_files_dir = self.get_musics_archive_folder()
        music_files_path_from_disk = []
        for entry in music_files_dir.iterdir():
            if entry.is_file() and entry.suffix in ACCEPTED_MUSIC_EXTENSIONS:
                music_files_path_from_disk.append(entry)
        return music_files_path_from_disk

    def get_all_ambient_music_files_in_archive(self):
        ambient_music_files_dir = self.get_ambient_musics_archive_folder()
        ambient_music_files_path_from_disk = []
        for entry in ambient_music_files_dir.iterdir():
            if entry.is_file() and entry.suffix in ACCEPTED_MUSIC_EXTENSIONS:
                ambient_music_files_path_from_disk.append(entry)
        return ambient_music_files_path_from_disk

    def clean_music_archive(self, music_objects_to_keep: List[MusicObject]):
        music_files_path_from_disk = self.get_all_music_files_in_archive()
        music_objects_to_keep_paths = [x.path for x in music_objects_to_keep]
        to_delete = [x for x in music_files_path_from_disk if x not in music_objects_to_keep_paths]
        [x.unlink() for x in to_delete]

    # Music Objects management
    def get_music_from_store(self, p_uid: uuid.UUID):
        if p_uid in self._stored_songs:
            return self._stored_songs[p_uid]
        else:
            return None

    def put_music_in_store(self, p_music_object: MusicObject):
        self._stored_songs[p_music_object.uid] = p_music_object

    def remove_music_from_store(self, p_music_object_uid: uuid.UUID):
        if p_music_object_uid in self._stored_songs:
            del self._stored_songs[p_music_object_uid]

    def add_music_to_store(self, p_original_path: Path) -> MusicObject:
        if p_original_path.exists() and p_original_path.suffix in ACCEPTED_MUSIC_EXTENSIONS:
            original_music_object = MusicObject(p_original_path)
            if original_music_object.uid not in self._stored_songs:
                target_path = self.get_musics_archive_folder() / f"{str(original_music_object.uid).replace('-', '')[0:16]}{p_original_path.suffix}"
                shutil.copy(p_original_path, target_path)
                final_music_object = original_music_object
                final_music_object.path = target_path
                self.put_music_in_store(final_music_object)
            else:
                final_music_object = self._stored_songs[original_music_object.uid]
            return final_music_object

    def load_all_available_songs_in_memory(self):
        songs_rows = self.db_get_all_songs()
        if len(songs_rows) > 0:
            as_is_songs = [MusicObject(p_definition_tuple=x) for x in songs_rows]
            music_files_path_from_disk = self.get_all_music_files_in_archive()
            if len(music_files_path_from_disk) > 0:
                songs_to_put_in_store = [x for x in as_is_songs if x.path in music_files_path_from_disk]
                [self.put_music_in_store(x) for x in songs_to_put_in_store]

    def add_music_to_db(self, p_music_object: MusicObject):
        self.db_insert_one_song(p_music_object)

    # Ambient Musics Management
    def put_ambient_music_in_store(self, p_ambient_music_object: MusicObject):
        self._stored_ambient_musics[p_ambient_music_object.uid] = p_ambient_music_object

    def add_ambient_music_to_store(self, p_original_path: Path) -> MusicObject:
        if p_original_path.exists() and p_original_path.suffix in ACCEPTED_MUSIC_EXTENSIONS:
            original_music_object = MusicObject(p_original_path)
            if original_music_object.uid not in self._stored_songs:
                target_path = self.get_ambient_musics_archive_folder() / f"{str(original_music_object.uid).replace('-', '')[0:16]}{p_original_path.suffix}"
                shutil.copy(p_original_path, target_path)
                final_music_object = original_music_object
                final_music_object.path = target_path
                self.put_ambient_music_in_store(final_music_object)
            else:
                final_music_object = self._stored_songs[original_music_object.uid]
            return final_music_object

    def load_all_available_ambient_music_in_memory(self):
        ambient_musics_rows = self.db_get_all_ambient_musics_rows()
        if len(ambient_musics_rows) > 0:
            selected = [x[-1] for x in ambient_musics_rows]
            p_definition_tuples = [x[:-1] for x in ambient_musics_rows]
            as_is_ambient_musics = [MusicObject(p_definition_tuple=x) for x in p_definition_tuples]
            ambient_music_files_path_from_disk = self.get_all_ambient_music_files_in_archive()
            if len(ambient_music_files_path_from_disk) > 0:
                songs_to_put_in_store = [x for x in as_is_ambient_musics if
                                         x.path in ambient_music_files_path_from_disk]
                [self.put_ambient_music_in_store(x) for x in songs_to_put_in_store]
                for i in range(len(selected)):
                    if selected[i] == 1:
                        self._selected_ambient_music = songs_to_put_in_store[i].uid
                        break

    def add_ambient_music_to_db(self, p_ambient_music_object: MusicObject):
        self.db_insert_one_ambient_music(p_ambient_music_object)

    def set_selected_ambient_music(self, p_ambient_music_object: MusicObject):
        self._selected_ambient_music = p_ambient_music_object.uid

    def get_selected_ambient_music(self):
        if self._selected_ambient_music != uuid.UUID(int=0) and len(self._stored_ambient_musics) > 0:
            return self._stored_ambient_musics[self._selected_ambient_music]
        else:
            return None

    # Playlist Management
    def get_playlist_from_store(self, p_uid: uuid.UUID):
        if p_uid in self._stored_playlists:
            return self._stored_playlists[p_uid]
        else:
            return None

    def get_all_playlists_from_store(self):
        all_playlists = []
        if len(self._stored_playlists) > 0:
            all_playlists = list(self._stored_playlists.values())
            all_playlists.sort(key=lambda x: x.creation_date)
        return all_playlists

    def get_number_of_playlists_in_store(self):
        return len(self._stored_playlists)

    def put_playlist_in_store(self, p_playlist: Playlist):
        self._stored_playlists[p_playlist.uid] = p_playlist

    def load_all_available_playlists_in_memory(self):
        playlists_rows = self.db_get_all_playlists()
        if len(playlists_rows) > 0:
            as_is_playlists = [Playlist(x[0], x[1], x[2]) for x in playlists_rows]
            [self.populate_one_playlist(x) for x in as_is_playlists]
            [self.put_playlist_in_store(x) for x in as_is_playlists]

    def populate_one_playlist(self, p_playlist: Playlist):
        songs_for_playlists_rows = self.db_get_one_playlist_songs(p_playlist.uid)
        if len(songs_for_playlists_rows) > 0:
            [p_playlist.add_song(uuid.UUID(x[0])) for x in songs_for_playlists_rows]

    def save_one_playlist(self, p_playlist_uid: uuid.UUID):
        p_playlist = self.get_playlist_from_store(p_playlist_uid)
        if p_playlist is not None and p_playlist.is_dirty:
            self.db_insert_one_playlist(p_playlist)
            self.db_delete_ps_entries_for_playlist(p_playlist)
            if not p_playlist.is_empty():
                [self.db_insert_one_ps_entry_for_playlist(p_playlist.uid, p_playlist.get_song(x), x) for x in
                 range(p_playlist.size())]

    def delete_one_playlist(self, p_playlist_uid: uuid.UUID):
        playlist = self.get_playlist_from_store(p_playlist_uid)
        if playlist is not None:
            self.db_delete_one_playlist(playlist)
            self.delete_playlist_from_store(p_playlist_uid)

    def delete_playlist_from_store(self, p_playlist_uid: uuid.UUID):
        if p_playlist_uid in self._stored_playlists:
            del self._stored_playlists[p_playlist_uid]

    # Save all
    def save_all(self):
        all_music_uuids_to_keep = []
        all_playlists_in_store = self.get_all_playlists_from_store()
        [all_music_uuids_to_keep.extend(x.get_all_songs()) for x in all_playlists_in_store]
        all_music_uuids_to_keep = set(all_music_uuids_to_keep)
        music_objects_to_keep = [self.get_music_from_store(x) for x in all_music_uuids_to_keep]
        [self.save_one_playlist(x) for x in [y.uid for y in all_playlists_in_store]]
        self.db_delete_all_songs()
        self.db_insert_many_songs(music_objects_to_keep)
        self.db_insert_many_ambient_musics(list(self._stored_ambient_musics.values()))
        return music_objects_to_keep

    # DB Operations
    # GENERAL
    def connect_to_db(self):
        conn = None
        try:
            conn = sqlite3.connect(self.get_db_file_path())
        except Error as e:
            print(e)

        return conn

    def init_db(self):
        self.db_create_table(sql_create_playlists_table)
        self.db_create_table(sql_create_songs_table)
        self.db_create_table(sql_create_playlists_songs_table)
        self.db_create_table(sql_create_break_musics_table)
        self.init_ambient_songs_db()

    def init_ambient_songs_db(self):
        preloaded_sounds_folder = self.get_preloaded_sounds_folder()
        ambient_rain_file_path = preloaded_sounds_folder / AMBIENT_RAIN_FILE_NAME
        ambient_shreksophone_file_path = preloaded_sounds_folder / AMBIENT_SHREKSOPHONE_FILE_NAME
        ambient_musics_rows = self.db_get_all_ambient_musics_rows()
        if len(ambient_musics_rows) == 0:
            final_ambient_music_1 = self.add_ambient_music_to_store(ambient_shreksophone_file_path)
            final_ambient_music_2 = self.add_ambient_music_to_store(ambient_rain_file_path)
            self._selected_ambient_music = final_ambient_music_1.uid
            self.db_insert_one_ambient_music(final_ambient_music_1)
            self.db_insert_one_ambient_music(final_ambient_music_2)

    def db_create_table(self, p_sql_create_table_request):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(p_sql_create_table_request)
            conn.close()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    # SONGS
    def db_get_one_song(self, p_music_object: MusicObject):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_select_a_song_by_id, str(p_music_object.uid))
            songs_rows = c.fetchall()
            conn.close()
            return songs_rows
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_get_all_songs(self):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_select_all_songs)
            songs_rows = c.fetchall()
            conn.close()
            return songs_rows
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_insert_one_song(self, p_music_object: MusicObject):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_insert_one_song, (
                str(p_music_object.uid), p_music_object.title, p_music_object.artist, p_music_object.duration,
                str(p_music_object.path)))
            conn.commit()
            conn.close()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_insert_many_songs(self, p_music_objects: List[MusicObject]):
        try:
            conn = self.connect_to_db()
            p_music_objects_tuples = [x.as_tuple() for x in p_music_objects]
            c = conn.cursor()
            c.executemany(sql_insert_one_song, p_music_objects_tuples)
            conn.commit()
            conn.close()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_delete_one_song(self, p_music_object: MusicObject):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_delete_one_song, str(p_music_object.uid))
            conn.commit()
            conn.close()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_delete_all_songs(self):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_delete_all_songs)
            conn.commit()
            conn.close()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    # AMBIENT_MUSICS
    def db_get_all_ambient_musics_rows(self):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_select_all_ambient_musics)
            ambient_musics_rows = c.fetchall()
            conn.close()
            return ambient_musics_rows
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_get_one_ambient_music(self, p_ambient_music: MusicObject):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_select_an_ambient_music_by_id, (str(p_ambient_music.uid),))
            ambient_musics_rows = c.fetchall()
            conn.close()
            return ambient_musics_rows
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_insert_one_ambient_music(self, p_ambient_music_object: MusicObject):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_insert_one_ambient_music,
                      (str(p_ambient_music_object.uid), p_ambient_music_object.title, p_ambient_music_object.artist,
                       p_ambient_music_object.duration,
                       str(p_ambient_music_object.path),
                       (0, 1)[self._selected_ambient_music == p_ambient_music_object.uid]))
            conn.commit()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_insert_many_ambient_musics(self, p_ambient_music_objects: List[MusicObject]):
        try:
            conn = self.connect_to_db()
            p_music_objects_tuples = [x.as_tuple() + ((0, 1)[self._selected_ambient_music == x.uid],) for x in
                                      p_ambient_music_objects]
            c = conn.cursor()
            c.executemany(sql_insert_one_ambient_music, p_music_objects_tuples)
            conn.commit()
            conn.close()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    # PLAYLISTS
    def db_get_one_playlist(self, p_playlist: Playlist):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_select_one_playlist_by_id, (str(p_playlist.uid),))
            playlists_rows = c.fetchall()
            conn.close()
            return playlists_rows
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_get_all_playlists(self):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_select_all_playlists)
            playlists_rows = c.fetchall()
            conn.close()
            return playlists_rows
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_insert_one_playlist(self, p_playlist: Playlist):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_insert_one_playlist, (str(p_playlist.uid), p_playlist.name, p_playlist.creation_date.timestamp()))
            conn.commit()
            conn.close()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_delete_one_playlist(self, p_playlist: Playlist):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_delete_one_playlist, (str(p_playlist.uid),))
            conn.commit()
            conn.close()
            self.db_delete_ps_entries_for_playlist(p_playlist)
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    # PLAYLIST_SONGS
    def db_get_one_playlist_songs(self, p_playlist_id: uuid.UUID):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_select_all_songs_for_playlist, (str(p_playlist_id),))
            playlist_songs_rows = c.fetchall()
            conn.close()
            return playlist_songs_rows
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_empty_playlist_songs_table(self):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_delete_all_ps_entries)
            conn.commit()
            conn.close()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_delete_ps_entries_for_playlist(self, p_playlist: Playlist):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_delete_ps_entries_for_playlist, (str(p_playlist.uid),))
            conn.commit()
            conn.close()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)

    def db_insert_one_ps_entry_for_playlist(self, p_playlist_uid, p_song_uid, p_position):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_insert_one_playlist_song_entry, (str(p_playlist_uid), str(p_song_uid), p_position))
            conn.commit()
        except Error as e:
            print(inspect.currentframe().f_code.co_name)
            print(e)
