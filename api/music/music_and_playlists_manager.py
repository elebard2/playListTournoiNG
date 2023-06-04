import uuid
from pathlib import Path
import sqlite3
from sqlite3 import Error
import shutil
from typing import List

from api.music.music_object import MusicObject
from api.music.playlist import Playlist
from api.util.singleton import Singleton
from config.config import MUSICS_AND_PLAYLISTS_DIR_NAME, MUSICS_ARCHIVE_DIR_NAME, DATABASE_MUSICS_FILE_NAME

# CREATE TABLE requests
sql_create_playlists_table = """ CREATE TABLE IF NOT EXISTS playlists (
                                        id TEXT PRIMARY KEY,
                                        name TEXT NOT NULL
                                    ); """

sql_create_songs_table = """CREATE TABLE IF NOT EXISTS songs (
                                    id TEXT PRIMARY KEY,
                                    title TEXT NOT NULL,
                                    artist TEXT NOT NULL,
                                    duration REAL NOT NULL,
                                    file_path TEXT NOT NULL,
                                    UNIQUE(file_path)
                                );"""

sql_create_playlists_songs_table = """CREATE TABLE IF NOT EXISTS playlist_songs (
                                        id integer PRIMARY KEY,
                                        playlist_id TEXT,
                                        song_id TEXT,
                                        playlist_position INTEGER NOT NULL,
                                        FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                                        FOREIGN KEY (song_id) REFERENCES songs (id),
                                        UNIQUE(playlist_id, song_id, playlist_position)
                                    );"""

# INSERT Requests
sql_insert_one_song = """INSERT OR IGNORE INTO songs(id,title,artist,duration,file_path)
                        VALUES(?,?,?,?,?) """

sql_insert_one_playlist = """INSERT OR IGNORE INTO playlists(id,name)
                            VALUES(?,?) """

sql_insert_one_playlist_song_entry = """INSERT OR IGNORE INTO playlist_songs(playlist_id,song_id,playlist_position)
                                    VALUES(?,?,?) """

# SELECT Requests
sql_select_all_songs = "SELECT * FROM songs"

sql_select_a_song_by_id = "SELECT * FROM songs WHERE id=?"

sql_select_all_playlists = "SELECT * FROM playlists"

sql_select_a_playlist_by_id = "SELECT * FROM playlists WHERE id=?"

sql_select_all_songs_for_playlist = """SELECT 
                                 song_id
                                 FROM playlist_songs
                                 WHERE playlist_id=?
                                 ORDER BY playlist_position"""

# DELETE Requests
sql_delete_one_song = """DELETE FROM songs WHERE id=?"""

sql_delete_all_songs = """DELETE FROM songs"""

sql_delete_one_playlist = """DELETE FROM playlists WHERE id=?"""

sql_delete_all_ps_entries = "DELETE FROM playlist_songs"

sql_delete_ps_entries_for_playlist = "DELETE FROM playlist_songs WHERE playlist_id=?"

sql_delete_ps_entries_for_song = "DELETE FROM playlist_songs WHERE song_id=?"


class MusicAndPlaylistsManager(Singleton):
    _base_dir: Path
    _stored_songs: dict
    _stored_playlists: dict

    # Start
    def start(self, p_base_dir):
        self._stored_songs = {}
        self._stored_playlists = {}
        self.set_base_dir(p_base_dir)
        self.load_all_available_songs_in_memory()
        self.load_all_available_playlists_in_memory()

    def stop(self):
        music_objects_to_keep = self.save_all()
        self.clean_music_archive(music_objects_to_keep)

    # Files Management
    def set_base_dir(self, p_base_dir):
        self._base_dir = p_base_dir / MUSICS_AND_PLAYLISTS_DIR_NAME

    def get_db_file_path(self):
        return self._base_dir / DATABASE_MUSICS_FILE_NAME

    def get_stored_musics_folder(self):
        return self._base_dir / MUSICS_ARCHIVE_DIR_NAME

    def get_all_music_files_in_archive(self):
        music_files_dir = self.get_stored_musics_folder()
        music_files_path_from_disk = []
        for entry in music_files_dir.iterdir():
            if entry.is_file() and entry.suffix in [".mp3", ".ogg", ".flac"]:
                music_files_path_from_disk.append(entry)
        return music_files_path_from_disk

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

    def add_music_to_store(self, p_original_path: Path) -> MusicObject:
        if p_original_path.exists() and p_original_path.suffix in [".mp3", ".ogg", ".flac"]:
            original_music_object = MusicObject(p_original_path)
            if original_music_object.uid not in self._stored_songs:
                target_path = self.get_stored_musics_folder() / f"{str(original_music_object.uid).replace('-', '')[0:16]}{p_original_path.suffix}"
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
            songs_to_put_in_store = [x for x in as_is_songs if x.path in music_files_path_from_disk]
            [self.put_music_in_store(x) for x in songs_to_put_in_store]

    def add_music_to_db(self, p_music_object: MusicObject):
        self.db_insert_one_song(p_music_object)

    # Playlist Management
    def get_playlist_from_store(self, p_uid: uuid.UUID):
        if p_uid in self._stored_playlists:
            return self._stored_playlists[p_uid]
        else:
            return None

    def get_all_playlists_from_store(self):
        if len(self._stored_playlists) > 0:
            all_playlists = list(self._stored_playlists.values())
        else:
            all_playlists = [Playlist()]
        return all_playlists

    def put_playlist_in_store(self, p_playlist: Playlist):
        self._stored_playlists[p_playlist.uid] = p_playlist

    def load_all_available_playlists_in_memory(self):
        playlists_rows = self.db_get_all_playlists()
        if len(playlists_rows) > 0:
            as_is_playlists = [Playlist(x[0], x[1]) for x in playlists_rows]
            [self.populate_one_playlist(x) for x in as_is_playlists]
            [self.put_playlist_in_store(x) for x in as_is_playlists]

    def populate_one_playlist(self, p_playlist: Playlist):
        songs_for_playlists_rows = self.db_get_one_playlist_songs(p_playlist.uid)
        if len(songs_for_playlists_rows) > 0:
            [p_playlist.add_song(uuid.UUID(x[0])) for x in songs_for_playlists_rows]

    def save_one_playlist(self, p_playlist: Playlist):
        if p_playlist is not None and p_playlist.is_dirty:
            self.db_insert_one_playlist( p_playlist)
            self.db_delete_ps_entries_for_playlist(p_playlist)
            if not p_playlist.is_empty():
                [self.db_insert_one_ps_entry_for_playlist(p_playlist.uid, p_playlist.get_song(x), x) for x in range(p_playlist.size())]

    def delete_one_playlist(self, p_playlist_uid: uuid.UUID):
        playlist = self.get_playlist_from_store(p_playlist_uid)
        if playlist is not None:
            self.db_delete_one_playlist( playlist)
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
        [self.save_one_playlist(x) for x in all_playlists_in_store]
        self.db_delete_all_songs()
        self.db_insert_many_songs(music_objects_to_keep)
        return music_objects_to_keep

    # DB Operations
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

    def db_create_table(self, p_sql_create_table_request):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(p_sql_create_table_request)
            conn.close()
        except Error as e:
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
            print(e)

    def db_insert_one_song(self, p_music_object: MusicObject):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_insert_one_song, (
                str(p_music_object.uid), p_music_object.title, p_music_object.artist, p_music_object.duration,
                p_music_object.path,))
            conn.commit()
            conn.close()
        except Error as e:
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
            print(e)

    def db_get_one_playlist_songs(self, p_playlist_id: uuid.UUID):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_select_all_songs_for_playlist, (str(p_playlist_id),))
            playlist_songs_rows = c.fetchall()
            conn.close()
            return playlist_songs_rows
        except Error as e:
            print(e)

    def db_delete_one_song(self, p_music_object: MusicObject):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_delete_one_song, (str(p_music_object.uid),))
            conn.commit()
            conn.close()
        except Error as e:
            print(e)

    def db_delete_all_songs(self):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_delete_all_songs)
            conn.commit()
            conn.close()
        except Error as e:
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
            print(e)

    def db_empty_playlist_songs_table(self):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_delete_all_ps_entries)
            conn.commit()
            conn.close()
        except Error as e:
            print(e)

    def db_delete_ps_entries_for_playlist(self, p_playlist: Playlist):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_delete_ps_entries_for_playlist, str(p_playlist.uid))
            conn.commit()
            conn.close()
        except Error as e:
            print(e)

    def db_insert_one_ps_entry_for_playlist(self, p_playlist_uid, p_song_uid, p_position):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_insert_one_playlist_song_entry, (str(p_playlist_uid), str(p_song_uid), p_position))
            conn.commit()
        except Error as e:
            print(e)

    def db_insert_one_playlist(self, p_playlist: Playlist):
        try:
            conn = self.connect_to_db()
            c = conn.cursor()
            c.execute(sql_insert_one_playlist, (str(p_playlist.uid), p_playlist.name))
            conn.commit()
            conn.close()
        except Error as e:
            print(e)
