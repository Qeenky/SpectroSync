import os
import subprocess
import tempfile


# Test Tools functions
def create_reverse_video(input_video, output_video, temp_dir=None):
    """
    Создает видео туда и обратно (прямое + обратное)

    Args:
        input_video: путь к исходному видео
        output_video: путь для сохранения результата
        temp_dir: временная папка (если None, создается автоматически)
    """
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()
    else:
        os.makedirs(temp_dir, exist_ok=True)

    reverse_video = os.path.join(temp_dir, "reverse.mp4")

    try:
        duration_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_video
        ]
        result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        print(f"📊 Исходное видео: {duration:.2f} сек")
        print("🔄 Создание обратной версии...")
        reverse_cmd = [
            'ffmpeg',
            '-i', input_video,
            '-vf', 'reverse',
            '-af', 'areverse',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'fast',
            '-crf', '18',
            reverse_video,
            '-y'
        ]
        subprocess.run(reverse_cmd, check=True, capture_output=True, text=True)

        if not os.path.exists(reverse_video):
            print("❌ Обратное видео не создалось")
            return False
        list_file = os.path.join(temp_dir, "concat.txt")
        with open(list_file, 'w') as f:
            f.write(f"file '{os.path.abspath(input_video).replace(chr(92), chr(92) * 2)}'\n")
            f.write(f"file '{os.path.abspath(reverse_video).replace(chr(92), chr(92) * 2)}'\n")

        print("🔗 Склейка видео...")

        concat_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-movflags', '+faststart',
            output_video,
            '-y'
        ]

        result = subprocess.run(concat_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"⚠️ Ошибка при прямой склейке, пробуем с перекодированием...")

            concat_cmd = [
                'ffmpeg',
                '-i', input_video,
                '-i', reverse_video,
                '-filter_complex',
                '[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]',
                '-map', '[v]',
                '-map', '[a]',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'fast',
                '-crf', '18',
                '-movflags', '+faststart',
                output_video,
                '-y'
            ]
            subprocess.run(concat_cmd, check=True, capture_output=True, text=True)

        if os.path.exists(output_video):
            result_duration_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                output_video
            ]
            result = subprocess.run(result_duration_cmd, capture_output=True, text=True, check=True)
            result_duration = float(result.stdout.strip())

            print(f"📊 Итоговое видео: {result_duration:.2f} сек")
            print(f"✅ Готово! Результат: {output_video}")
            return True
        else:
            print("❌ Ошибка: выходной файл не создан")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка FFmpeg: {e}")
        if e.stderr:
            print(f"Детали: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False
    finally:
        try:
            if os.path.exists(reverse_video):
                os.remove(reverse_video)
            if os.path.exists(list_file):
                os.remove(list_file)
            if temp_dir and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass


def slow_down_video_simple(input_video, output_video, speed_factor=0.5):
    try:
        print(f"🐢 Замедление видео в {1 / speed_factor:.1f} раз...")

        slow_cmd = [
            'ffmpeg',
            '-i', input_video,
            '-filter:v', f'setpts={speed_factor}*PTS',
            '-filter:a', f'atempo={1 / speed_factor}',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'fast',
            '-crf', '18',
            output_video,
            '-y'
        ]

        subprocess.run(slow_cmd, check=True, capture_output=True)
        print(f"✅ Готово: {output_video}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        if e.stderr:
            print(f"Детали: {e.stderr.decode()}")
        return False


def trim_video_reencode(input_video, output_video, start_time=0, end_time=None, duration=None):
    """
    Обрезает видео по времени с перекодированием (более точное, но медленнее)

    Args:
        input_video: путь к исходному видео
        output_video: путь для сохранения результата
        start_time: время начала в секундах
        end_time: время конца в секундах
        duration: длительность обрезки в секундах
    """
    try:
        if end_time is None and duration is None:
            print("❌ Укажите end_time или duration")
            return False

        duration_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_video
        ]
        result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        total_duration = float(result.stdout.strip())

        if end_time is not None:
            trim_end = min(end_time, total_duration)
            trim_duration = trim_end - start_time
        else:
            trim_duration = min(duration, total_duration - start_time)
            trim_end = start_time + trim_duration

        if start_time < 0 or start_time >= total_duration:
            print(f"❌ Некорректное start_time: {start_time}")
            return False

        print(f"✂️ Обрезка видео (с перекодированием):")
        print(f"   Начало: {start_time:.2f} сек")
        print(f"   Конец: {trim_end:.2f} сек")
        print(f"   Длительность: {trim_duration:.2f} сек")

        trim_cmd = [
            'ffmpeg',
            '-i', input_video,
            '-ss', str(start_time),
            '-t', str(trim_duration),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'fast',
            '-crf', '18',
            output_video,
            '-y'
        ]

        subprocess.run(trim_cmd, check=True, capture_output=True)

        print(f"✅ Готово! Результат: {output_video}")
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    trim_video_reencode("input_data/temp.mp4", "input_data/temp1.mp4", end_time=3)
    create_reverse_video(
        input_video="input_data/temp1.mp4",
        output_video="input_data/backv1.mp4"
    )
    slow_down_video_simple("input_data/backv1.mp4", "input_data/backv.mp4", speed_factor=1.4)