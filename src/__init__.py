from .core.models import MediaAsset, VideoConfig
from .core.interfaces import IMediaRepository, IVideoCreator
from .repositories.simple_repository import SimpleMediaRepository
from .creators.ffmpeg_creator import FFmpegVideoCreator


__version__ = "1.0.0"
__author__ = "Qeenky"

__all__ = [
    # Модели
    'MediaAsset',
    'VideoConfig',

    # Интерфейсы
    'IMediaRepository',
    'IVideoCreator',

    # Репозитории
    'SimpleMediaRepository',

    # Создатели
    'FFmpegVideoCreator',
]