from src.core.interfaces import IVideoCreator, IMediaRepository
from src.core.models import VideoConfig
import subprocess




class FFmpegVideoCreator(IVideoCreator):
    def __init__(self, repository: IMediaRepository):
        self._repo = repository

    def create_video(self, config: VideoConfig) -> bool:
        image = self._repo.get_image()
        audio = self._repo.get_audio()

        if not image:
            raise ValueError("Image not set")
        if not audio:
            raise ValueError("Audio not set")

        audio_duration = self._get_audio_duration(audio.path)

        quality_params = self._get_max_quality_params(config)

        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', image.path,
            '-i', audio.path,
            *quality_params,
            '-t', audio_duration,
            '-shortest',
            '-y',
            config.output_path
        ]

        print(f"Запуск команды: {' '.join(cmd[:10])}...")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=3600
            )
            print(f"+ Видео создано: {config.output_path}")
            return True

        except subprocess.TimeoutExpired:
            print("- Превышено время кодирования (1 час)")
            return False
        except subprocess.CalledProcessError as e:
            print(f"- Ошибка FFmpeg:")
            print(e.stderr[:500])
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

    def create_ultra_quality(self,
                             output_path: str = "ultra_quality.mp4",
                             resolution: tuple = (1920, 1080),
                             fps: int = 60) -> bool:
        config = VideoConfig(
            output_path=output_path,
            resolution=resolution,
            fps=fps,
            video_codec="libx264",
            audio_codec="aac"
        )
        return self.create_video(config)

    def create_lossless(self,
                        output_path: str = "lossless.mkv",
                        resolution: tuple = (1920, 1080)) -> bool:
        image = self._repo.get_image()
        audio = self._repo.get_audio()

        if not image or not audio:
            return False

        audio_duration = self._get_audio_duration(audio.path)

        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-framerate', '1',
            '-i', image.path,
            '-i', audio.path,
            '-c:v', 'ffv1',
            '-level', '3',
            '-coder', '1',
            '-context', '1',
            '-g', '1',
            '-slices', '24',
            '-slicecrc', '1',
            '-pix_fmt', 'bgr0',
            '-c:a', 'flac',
            '-compression_level', '12',
            '-ar', '96000',

            '-s', f"{resolution[0]}x{resolution[1]}",

            '-t', audio_duration,
            '-shortest',
            '-y',
            output_path
        ]

        print("- Создание lossless видео. Файл будет ОГРОМНЫМ!")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"+ Lossless видео создано: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"- Ошибка: {e.stderr[:500]}")
            return False

    def create_4k_hdr(self,
                      output_path: str = "4k_hdr.mp4",
                      hdr: bool = True) -> bool:
        config = VideoConfig(
            output_path=output_path,
            resolution=(3840, 2160),
            fps=60,
            video_codec="libx265",
            audio_codec="aac"
        )
        quality_params = [
            '-c:v', 'libx265',
            '-crf', '20',
            '-preset', 'slow',
            '-profile:v', 'main10',
            '-pix_fmt', 'yuv420p10le',
            '-tag:v', 'hvc1',
        ]
        if hdr:
            quality_params.extend([
                '-colorspace', 'bt2020nc',
                '-color_primaries', 'bt2020',
                '-color_trc', 'smpte2084',
                '-color_range', 'tv',
            ])

        old_method = self._get_max_quality_params
        self._get_max_quality_params = lambda cfg: quality_params + [
            '-c:a', 'aac',
            '-b:a', '320k',
            '-ar', '48000',
            '-s', f"{cfg.resolution[0]}x{cfg.resolution[1]}",
            '-r', str(cfg.fps),
        ]

        try:
            result = self.create_video(config)
            return result
        finally:
            self._get_max_quality_params = old_method

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