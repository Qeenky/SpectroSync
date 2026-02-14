from typing import Tuple

import librosa

class Analizator:
    def __init__(self):
        self.audio_path = None
        self.spectrogram = None
        self.audio = None
        self.sr = None
        self.low_bands = None
        self.medium_bands = None
        self.high_bands = None


    def _set_audio_path(self, audio_path: str):
        self.audio_path = audio_path

    def _precompute_all_powers(self):
        self._get_spectrogram()
        if self.spectrogram is None:
            return
        low_bands = self.spectrogram[:30, :]
        medium_bands = self.spectrogram[30:60, :]
        high_bands = self.spectrogram[60:128, :]
        self.low_bands = low_bands.mean(axis=0)
        self.medium_bands = medium_bands.mean(axis=0)
        self.high_bands = high_bands.mean(axis=0)

    def _get_audio_sr(self) -> Tuple:
        if self.audio_path is None:
            return tuple()
        self.audio, self.sr = librosa.load(self.audio_path)
        return tuple([self.audio, self.sr])

    def _get_spectrogram(self):
        self._get_audio_sr()
        if self.audio is None or self.sr is None:
            return None
        self.spectrogram = librosa.feature.melspectrogram(y=self.audio, sr=self.sr)
        return self.spectrogram

    def _show_spectrogram(self):
        self._get_spectrogram()
        if self.spectrogram is None:
            return
        print(self.spectrogram.shape)

    def _show_first_frame_spectrogram(self):
        self._get_spectrogram()
        if self.spectrogram is None:
            return
        print(self.spectrogram[:, 0])

    def _get_power_by_frame(self, frame_index: int) -> float:
        if hasattr(self, 'all_powers'):
            return self.all_powers[frame_index]
        return 0.0

    def _get_power_by_time(self, time_sec: float) -> dict:
        """:return {low:..., medium:..., high:...}"""

        if not hasattr(self, 'all_powers'):
            return dict()
        frame_index_low = int(time_sec * self.sr / 512)
        frame_index_medium = int(time_sec * self.sr / 512)
        frame_index_high = int(time_sec * self.sr / 512)
        if frame_index_low >= len(self.low_bands):
            frame_index_low = len(self.low_bands) - 1
        if frame_index_medium >= len(self.medium_bands):
            frame_index_medium = len(self.medium_bands) - 1
        if frame_index_high >= len(self.high_bands):
            frame_index_high = len(self.high_bands) - 1

        return {"low":self.low_bands[frame_index_low],
                "medium":self.medium_bands[frame_index_medium],
                "high":self.high_bands[frame_index_high]}

    def _get_audio_duration(self) -> float:
        if self.spectrogram is None or self.sr is None:
            return 0.0
        return self.spectrogram.shape[1] * 512 / self.sr



