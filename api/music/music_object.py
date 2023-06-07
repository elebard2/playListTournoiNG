from math import floor
from pathlib import Path
import audio_metadata
import uuid
import hashlib

from api.music.music_exceptions import MusicLoadError, NotAMusicFileError, MusicTupleDefinitionError, MusicNoValidInputsError


class MusicObject:
    _path_to_file: Path
    _title: str
    _duration: float
    _artist: str
    _uid: uuid.UUID

    def __init__(self, p_path_to_file: Path = None, p_definition_tuple: tuple = None):
        self._uid = uuid.UUID(int=0)
        self._path_to_file = None
        self._title = ""
        self._artist = ""
        self._duration = -1.0
        if p_path_to_file is not None and isinstance(p_path_to_file, Path):
            if p_path_to_file.exists():
                self._path_to_file = p_path_to_file
                self.set_from_metadata()
            else:
                raise MusicLoadError(p_path_to_file)
        elif p_definition_tuple is not None and isinstance(p_definition_tuple, tuple):
            if len(p_definition_tuple) == 5:
                try:
                    self.uid = uuid.UUID(p_definition_tuple[0])
                    self.title = p_definition_tuple[1]
                    self.artist = p_definition_tuple[2]
                    self.duration = float(p_definition_tuple[3])
                    self.path = Path(p_definition_tuple[4])
                except ValueError:
                    raise MusicTupleDefinitionError(p_definition_tuple)
            else:
                raise MusicTupleDefinitionError(p_definition_tuple)
        else:
            raise MusicNoValidInputsError

    @property
    def path(self):
        return self._path_to_file

    @path.setter
    def path(self, p_path):
        if isinstance(p_path, Path) and p_path.exists():
            self._path_to_file = p_path
        else:
            raise ValueError

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, p_title):
        if isinstance(p_title, str):
            self._title = p_title
        else:
            raise ValueError

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, p_duration):
        if (isinstance(p_duration, float) or isinstance(p_duration, int)) and p_duration > 0:
            self._duration = float(p_duration)
        else:
            raise ValueError

    @property
    def artist(self):
        return self._artist

    @artist.setter
    def artist(self, p_artist):
        if isinstance(p_artist, str):
            self._artist = p_artist
        else:
            raise ValueError

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, p_id):
        if isinstance(p_id, uuid.UUID):
            self._uid = p_id
        else:
            raise ValueError

    def set_from_metadata(self):
        try:
            metadata = audio_metadata.load(self._path_to_file)
            tags = metadata.tags
            try:
                self.artist = tags.artist[0]
            except AttributeError:
                self.artist = "<Inconnu>"
            try:
                self.title = tags.title[0]
            except AttributeError:
                self.title = self._path_to_file.stem
            stream_info = metadata.streaminfo
            self.duration = stream_info.duration
            self.compute_id()
        except TypeError:
            raise NotAMusicFileError(self._path_to_file)

    def format_duration(self):
        if self._duration is not None and isinstance(self._duration, float) and self._duration > 0:
            hours = int(self._duration) // 3600
            minutes = (int(self._duration) - 3600 * hours) // 60
            seconds = int(self._duration) - 3600 * hours - 60 * minutes

            if hours == 0:
                str_hours = None
            elif hours < 10:
                str_hours = f"0{hours}"
            else:
                str_hours = f"{hours}"

            if minutes < 10:
                str_minutes = f"0{minutes}"
            else:
                str_minutes = f"{minutes}"

            if seconds < 10:
                str_seconds = f"0{seconds}"
            else:
                str_seconds = f"{seconds}"

            if str_hours is None:
                str_duration = f"{str_minutes}:{str_seconds}"
            else:
                str_duration = f"{str_hours}:{str_minutes}:{str_seconds}"

            return str_duration

    def compute_id(self):
        if self.artist is not None and self.title is not None and self.duration is not None:
            str_for_sha = f"{self._artist};{self._title};{self._duration}"
            hash_value = hashlib.sha256(str_for_sha.encode())
            self.uid = uuid.UUID(hash_value.hexdigest()[::2])

    def as_tuple(self):
        the_tuple = (str(self.uid), self.title, self.artist, self.duration, str(self.path))
        return the_tuple
