from abc import ABC, abstractmethod
from typing import Optional

from src.core.models import MediaAsset, VideoConfig


class IMediaRepository(ABC):
    @abstractmethod
    def get_image(self) -> Optional[MediaAsset]:
        pass

    @abstractmethod
    def get_audio(self) -> Optional[MediaAsset]:
        pass


class IVideoCreator(ABC):
    @abstractmethod
    def create_video(self, config: VideoConfig) -> bool:
        pass