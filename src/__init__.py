from .core.models import MediaAsset, VideoConfig
from .core.interfaces import IMediaRepository, IVideoCreator
from .repositories.simple_repository import SimpleMediaRepository
from .repositories.file_repository import  FileMediaRepository
from .creators.ffmpeg_creator import FFmpegVideoCreator
from .creators.advanced_creator import AdvancedVideoCreator
from .creators.advanced_creator import VideoCreationFacade

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
    'FileMediaRepository',

    # Создатели
    'FFmpegVideoCreator',
    'AdvancedVideoCreator',

    # Фасад
    'VideoCreationFacade',
]