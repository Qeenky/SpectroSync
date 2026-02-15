from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class MediaAsset:
    path: str
    duration: Optional[float] = None
    resolution: Optional[tuple] = None


@dataclass
class VideoConfig:
    output_path: str
    resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"

    # Параметры качества
    crf: int = 18
    preset: str = "slow"
    bitrate_audio: str = "320k"
    metadata_title: Optional[str] = None

    # Параметры волн
    enable_waves: bool = False
    wave_height_ratio: float = 0.20
    wave_position: str = "bottom"  # "bottom" или "top"