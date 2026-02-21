from typing import Optional
from src.core.models import MediaAsset
from src.core.interfaces import IMediaRepository
import os


class SimpleMediaRepository(IMediaRepository):
    def __init__(self):
        self._image: Optional[MediaAsset] = None
        self._audio: Optional[MediaAsset] = None
        self._video_input: Optional[MediaAsset] = None  # Новое поле

    def set_image(self, image_path: str) -> None:
        if os.path.exists(image_path) and image_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self._image = MediaAsset(path=image_path)
        else:
            raise ValueError(f"Invalid image file: {image_path}")

    def set_audio(self, audio_path: str) -> None:
        if os.path.exists(audio_path) and audio_path.lower().endswith(('.mp3', '.wav', '.flac')):
            self._audio = MediaAsset(path=audio_path)
        else:
            raise ValueError(f"Invalid audio file: {audio_path}")

    def set_video_input(self, video_path: str) -> None:
        """Устанавливает видео для зацикливания"""
        if os.path.exists(video_path) and video_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            self._video_input = MediaAsset(path=video_path)
        else:
            raise ValueError(f"Invalid video file: {video_path}")

    def get_image(self) -> Optional[MediaAsset]:
        return self._image

    def get_audio(self) -> Optional[MediaAsset]:
        return self._audio

    def get_video_input(self) -> Optional[MediaAsset]:
        return self._video_input