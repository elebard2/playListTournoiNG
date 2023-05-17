
class MusicLoadError(Exception):

    def __init__(self, p_path_to_music):
        self.unavailable_path = p_path_to_music
        self.message = f"Path {self.unavailable_path} is not available"
        super().__init__(self.message)


class NotAMusicFileError(Exception):

    def __init__(self, p_path_to_file):
        self.not_a_music_file_path = p_path_to_file
        self.message = f"Path {self.not_a_music_file_path} is not a music file"
        super().__init__(self.message)