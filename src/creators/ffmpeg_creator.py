from src.core.interfaces import IVideoCreator, IMediaRepository
from src.core.models import VideoConfig
import subprocess


class FFmpegVideoCreator(IVideoCreator):
    def __init__(self, repository: IMediaRepository):
        self._repo = repository

    def create_video(self, config: VideoConfig, scale_mode='crop') -> bool:
        """
        Создает видео из изображения или зацикленного видео с аудиодорожкой

        scale_mode: 'stretch' - растянуть, 'crop' - обрезать, 'pad' - черные полосы
        """
        image = self._repo.get_image()
        audio = self._repo.get_audio()
        video_input = self._repo.get_video_input()

        if not audio:
            raise ValueError("Audio not set")

        if not image and not video_input:
            raise ValueError("Either image or video input must be set")

        audio_duration = self._get_audio_duration(audio.path)
        quality_params = self._get_max_quality_params(config)
        filter_complex = self._get_scale_filter(scale_mode)

        if video_input:
            cmd = [
                'ffmpeg',
                '-stream_loop', '-1',
                '-i', video_input.path,
                '-i', audio.path,
            ]
            if filter_complex:
                cmd.extend(['-filter_complex', f'[0:v]{filter_complex}[v]'])
                cmd.extend(['-map', '[v]'])
            else:
                cmd.extend(['-map', '0:v'])

        else:
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', image.path,
                '-i', audio.path,
            ]

            if filter_complex:
                cmd.extend(['-vf', filter_complex])

        common_params = [
            '-map', '1:a',
            *quality_params,
            '-t', audio_duration,
            '-shortest',
            '-y',
            config.output_path
        ]

        cmd.extend(common_params)

        print(f"Запуск команды: {' '.join(cmd[:10])}...")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=3600
            )

            input_type = "видео" if video_input else "изображения"
            print(f"+ Видео создано из {input_type}: {config.output_path}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"- Ошибка FFmpeg: {e.stderr}")
            return False
        except Exception as e:
            print(f"- Ошибка: {e}")
            return False

    def _get_scale_filter(self, scale_mode: str) -> str:
        """Возвращает фильтр масштабирования в зависимости от режима"""
        if scale_mode == 'stretch':
            return "scale=1920:1080,setsar=1:1,format=yuv420p"
        elif scale_mode == 'crop':
            return (
                "crop=min(iw\\,ih*16/9):min(ih\\,iw*9/16),"
                "scale=1920:1080,"
                "format=yuv420p"
            )
        elif scale_mode == 'pad':
            return (
                "scale=1920:1080:force_original_aspect_ratio=1,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
                "format=yuv420p"
            )
        return ""

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

    def overlay_videos(self, main_video, overlay_video, output_video, custom_x=0, custom_y=0,
                       overlay_width=None, overlay_height=None):
        """
        Наложение видео с прозрачностью на основное видео

        Args:
            main_video: путь к основному видео
            overlay_video: путь к видео для наложения
            output_video: путь для сохранения результата
            custom_x: позиция X для наложения
            custom_y: позиция Y для наложения
            overlay_width: ширина накладываемого видео (если None, сохраняется оригинальная)
            overlay_height: высота накладываемого видео (если None, сохраняется оригинальная)
        """
        print(f"🎬 Наложение видео с прозрачностью...")

        scale_filter = ""
        if overlay_width and overlay_height:
            scale_filter = f"scale={overlay_width}:{overlay_height},"
            print(f"📐 Масштабирование: {overlay_width}x{overlay_height}")

        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            overlay_video
        ]

        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            dimensions = result.stdout.strip().split(',')
            if len(dimensions) == 2:
                width, height = dimensions
                print(f"📐 Оригинальный размер оверлея: {width}x{height}")
        except:
            pass

        ffmpeg_cmd = [
            'ffmpeg',
            '-i', main_video,
            '-i', overlay_video,
            '-filter_complex',
            f'[1:v]format=rgba,{scale_filter}setdar=1[over]; '
            f'[0:v]scale=1920:1080,format=yuva420p[main]; '
            f'[main][over]overlay={custom_x}:{custom_y}:format=auto,format=yuv420p[out]',
            '-map', '[out]',
            '-map', '0:a?',
            '-c:v', 'libx264',
            '-crf', '18',
            '-preset', 'slow',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            '-y',
            output_video
        ]

        try:
            result = subprocess.run(
                ffmpeg_cmd,
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Видео успешно создано: {output_video}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка при выполнении FFmpeg:")
            print(f"STDERR: {e.stderr}")
            print("🔄 Пробую альтернативный метод наложения...")
            alt_cmd = [
                'ffmpeg',
                '-i', main_video,
                '-i', overlay_video,
                '-filter_complex',
                f'[1:v]format=rgba,{scale_filter}[over]; '
                f'[0:v][over]overlay={custom_x}:{custom_y}:format=auto,'
                f'colorchannelmixer=aa=1[out]',
                '-map', '[out]',
                '-map', '0:a?',
                '-c:v', 'libx264',
                '-crf', '18',
                '-preset', 'slow',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-movflags', '+faststart',
                '-y',
                output_video
            ]

            try:
                subprocess.run(alt_cmd, check=True, capture_output=True, text=True)
                print(f"✅ Видео успешно создано (альтернативный метод): {output_video}")
                return True
            except subprocess.CalledProcessError as e2:
                print(f"❌ Ошибка и в альтернативном методе: {e2.stderr}")
                return False
            except FileNotFoundError:
                print("❌ FFmpeg не найден. Убедитесь что FFmpeg установлен и доступен в PATH")
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