from typing import Tuple

import librosa

class Analizator:
    def __init__(self):
        self.audio_path = None
        self.spectrogram = None
        self.audio = None
        self.sr = None
        self.all_powers = None

    def _set_audio_path(self, audio_path: str):
        self.audio_path = audio_path

    def _precompute_all_powers(self):
        self._get_spectrogram()
        if self.spectrogram is None:
            return
        low_bands = self.spectrogram[:30, :]
        self.all_powers = low_bands.mean(axis=0)

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

    def _get_power_by_time(self, time_sec: float) -> float:
        if not hasattr(self, 'all_powers'):
            return 0.0
        frame_index = int(time_sec * self.sr / 512)
        if frame_index >= len(self.all_powers):
            frame_index = len(self.all_powers) - 1
        return self.all_powers[frame_index]

    def _get_audio_duration(self) -> float:
        if self.spectrogram is None or self.sr is None:
            return 0.0
        return self.spectrogram.shape[1] * 512 / self.sr



