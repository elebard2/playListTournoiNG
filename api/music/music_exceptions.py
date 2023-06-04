class MusicError(Exception):

    def __init__(self, p_message):
        self.message = p_message
        super().__init__(self.message)


class MusicLoadError(MusicError):

    def __init__(self, p_path_to_music):
        self.unavailable_path = p_path_to_music
        self.message = f"Path {self.unavailable_path} is not available"
        super().__init__(self.message)


class MusicTupleDefinitionError(MusicError):

    def __init__(self, p_definition_tuple):
        self.p_definition_tuple = p_definition_tuple
        self.message = f"Definition Tuple {self.p_definition_tuple} is not valid"
        super().__init__(self.message)


class MusicNoValidInputsError(MusicError):

    def __init__(self):
        self.message = "The provided input is not valid for any definition of a MusicObject"
        super().__init__(self.message)


class NotAMusicFileError(MusicError):

    def __init__(self, p_path_to_file):
        self.not_a_music_file_path = p_path_to_file
        self.message = f"Path {self.not_a_music_file_path} is not a music file"
        super().__init__(self.message)
