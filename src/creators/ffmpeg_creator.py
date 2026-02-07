from core.interfaces import IVideoCreator, IMediaRepository
from core.models import VideoConfig
import subprocess




class FFmpegVideoCreator(IVideoCreator):
    def __init__(self, repository: IMediaRepository):
        self._repo = repository

    def create_video(self, config: VideoConfig) -> bool:
        """Создание видео из изображения и аудио"""
        image = self._repo.get_image()
        audio = self._repo.get_audio()

        if not image:
            raise ValueError("Image not set")
        if not audio:
            raise ValueError("Audio not set")

        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', image.path,
            '-i', audio.path,
            '-c:v', config.video_codec,
            '-c:a', config.audio_codec,
            '-t', self._get_audio_duration(audio.path),
            '-s', f"{config.resolution[0]}x{config.resolution[1]}",
            '-r', str(config.fps),
            '-shortest',
            '-y',
            config.output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Video created successfully: {config.output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating video: {e.stderr}")
            return False

    def _get_audio_duration(self, audio_path: str) -> str:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return str(int(float(result.stdout.strip())))