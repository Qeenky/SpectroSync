from typing import Tuple

import librosa

class Analizator:
    def __init__(self):
        self.audio_path = None
        self.spectrogram = None
        self.audio = None
        self.sr = None

    def _set_audio_path(self, audio_path: str):
        self.audio_path = audio_path

    def _get_audio_sr(self) -> Tuple:
        if self.audio_path is None:
            return tuple()
        self.audio, self.sr = librosa.load(self.audio_path)
        return tuple([self.audio, self.sr])

    def _get_spectrogram(self):
        if self.audio is None or self.sr is None:
            return None
        self.spectrogram = librosa.feature.melspectrogram(y=self.audio, sr=self.sr)
        return self.spectrogram

    def _show_spectrogram(self):
        if self.spectrogram is None:
            return
        print(self.spectrogram.shape)

    def _show_first_frame_spectrogram(self):
        if self.spectrogram is None:
            return
        print(self.spectrogram[:, 0])

# Test
a = Analizator()
a._set_audio_path("") #absolute path
a._get_audio_sr()
a._get_spectrogram()
a._show_spectrogram()
a._show_first_frame_spectrogram()