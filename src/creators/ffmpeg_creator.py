from src.core.interfaces import IVideoCreator, IMediaRepository
from src.core.models import VideoConfig
import subprocess




class FFmpegVideoCreator(IVideoCreator):
    def __init__(self, repository: IMediaRepository):
        self._repo = repository

    def create_video(self, config: VideoConfig, scale_mode='pad') -> bool:
        """
        scale_mode: 'stretch' - растянуть, 'crop' - обрезать, 'pad' - черные полосы
        """
        image = self._repo.get_image()
        audio = self._repo.get_audio()

        if not image or not audio:
            raise ValueError("Image or Audio not set")

        audio_duration = self._get_audio_duration(audio.path)
        quality_params = self._get_max_quality_params(config)

        if scale_mode == 'stretch':
            filter_complex = "scale=1920:1080,setsar=1:1,format=yuv420p"
        elif scale_mode == 'crop':
            filter_complex = (
                "crop=min(iw\\,ih*16/9):min(ih\\,iw*9/16),"
                "scale=1920:1080,"
                "format=yuv420p"
            )
        else:
            filter_complex = (
                "scale=1920:1080:force_original_aspect_ratio=1,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
                "format=yuv420p"
            )

        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', image.path,
            '-i', audio.path,
            '-vf', filter_complex,
            *quality_params,
            '-t', audio_duration,
            '-shortest',
            '-y',
            config.output_path
        ]

        print(f"Запуск команды: {' '.join(cmd[:10])}...")

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=3600
            )
            print(f"+ Видео создано: {config.output_path}")
            return True
        except Exception as e:
            print(f"- Ошибка: {e}")
            return False

    def _get_max_quality_params(self, config: VideoConfig) -> list:
        return [
            '-c:v', 'libx264',
            '-crf', '18',
            '-preset', 'slow',
            '-profile:v', 'high',
            '-pix_fmt', 'yuv420p',
            '-tune', 'film',

            '-x264opts', 'aq-mode=3:psy-rd=1.0:deblock=-1,-1',

            '-s', f"{config.resolution[0]}x{config.resolution[1]}",
            '-r', str(config.fps),

            '-c:a', 'aac',
            '-b:a', '320k',
            '-ar', '48000',
            '-ac', '2',

            '-metadata', f'title={config.output_path}',
            '-movflags', '+faststart'
        ]


    def overlay_videos(self, main_video, overlay_video, output_video, overlay_position='bottom'):
        """
        Наложение видео с волнами на основное видео

        Args:
            main_video: путь к основному видео (1920x1080)
            overlay_video: путь к видео с волнами (1920x270)
            output_video: путь для сохранения результата
            overlay_position: 'top' (сверху) или 'bottom' (снизу)
        """

        if overlay_position == 'bottom':
            y_position = '810'
        else:
            y_position = '0'

        ffmpeg_cmd = [
            'ffmpeg',
            '-i', main_video,
            '-i', overlay_video,
            '-filter_complex',
            f'[1:v]format=rgba,scale=1920:270[over]; [0:v]scale=1920:1080[main]; [main][over]overlay=0:{y_position}:format=auto,format=yuv420p[out]',
            '-map', '[out]',
            '-map', '0:a?',
            '-c:v', 'libx264',
            '-crf', '18',
            '-preset', 'slow',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            '-y',
            output_video
        ]

        try:
            subprocess.run(
                ffmpeg_cmd,
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Видео успешно создано: {output_video}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Ошибка при выполнении FFmpeg:")
            print(f"STDERR: {e.stderr}")
            return False
        except FileNotFoundError:
            print("FFmpeg не найден. Убедитесь что FFmpeg установлен и доступен в PATH")
            return False


    def _get_audio_duration(self, audio_path: str) -> str:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            return str(int(duration))
        except:
            return "10"