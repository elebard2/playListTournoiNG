from pathlib import Path
import audio_metadata

from api.music.music_exceptions import MusicLoadError, NotAMusicFileError


class MusicObject:
    _path_to_file: Path
    _title: str
    _duration: float
    _artist: str

    def __init__(self, p_path_to_file: Path):
        if p_path_to_file.exists():
            self._path_to_file = p_path_to_file
            self.set_from_metadata()
        else:
            raise MusicLoadError(p_path_to_file)

    @property
    def path(self):
        return self._path_to_file

    @path.setter
    def path(self, p_path):
        if isinstance(p_path, Path):
            self._path_to_file = p_path

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, p_title):
        if isinstance(p_title, str):
            self._title = p_title

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, p_duration):
        if isinstance(p_duration, float) and p_duration > 0:
            self._duration = p_duration

    @property
    def artist(self):
        return self._artist

    @artist.setter
    def artist(self, p_artist):
        if isinstance(p_artist, str):
            self._artist = p_artist

    def set_from_metadata(self):
        try:
            metadata = audio_metadata.load(self._path_to_file)
            tags = metadata.tags
            try:
                self.artist = tags.artist
            except AttributeError:
                self.artist = "<Inconnu>"
            try:
                self.title = tags.title
            except AttributeError:
                self.title = self._path_to_file.stem
            streaminfo = metadata.streaminfo
            self.duration = streaminfo.duration
        except TypeError:
            raise NotAMusicFileError(self._path_to_file)

    def format_duration(self):
        if self.duration is not None and isinstance(self.duration, float) and self.duration > 0:
            minutes = int(self.duration / 60)
            hours = int(minutes / 60)
            seconds = int(self.duration % 60)

            if hours <= 0:
                str_hours = None
            else:
                str_hours = f"{hours}"
                minutes = minutes - 60 * hours
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

    def dict(self):
        return {'path': str(self.path)}
