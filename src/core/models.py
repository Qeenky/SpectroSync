from dataclasses import dataclass
from typing import Optional

@dataclass
class MediaAsset:
    path: str
    duration: Optional[float] = None
    resolution: Optional[tuple] = None


@dataclass
class VideoConfig:
    output_path: str = "output.mp4"
    resolution: tuple = (1920, 1080)
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"