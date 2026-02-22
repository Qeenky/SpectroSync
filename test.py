import os
import subprocess

# Test Tools functions
def create_reverse_with_fade(input_video, output_video, fade_duration=1.0, temp_dir="temp_reverse"):
    """
    Создает видео с плавным переходом между прямой и обратной версией

    Args:
        input_video: путь к исходному видео
        output_video: путь для сохранения результата
        fade_duration: длительность перехода в секундах
        temp_dir: временная папка
    """
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

        print(f"📊 Длительность видео: {duration:.2f} сек")
        print("🔄 Создание обратной версии...")

        reverse_cmd = [
            'ffmpeg',
            '-i', input_video,
            '-vf', 'reverse',
            '-af', 'areverse',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'fast',
            reverse_video,
            '-y'
        ]
        subprocess.run(reverse_cmd, check=True, capture_output=True)

        list_file = os.path.join(temp_dir, "concat_list.txt")
        with open(list_file, 'w') as f:
            f.write(f"file '{os.path.abspath(input_video)}'\n")
            f.write(f"file '{os.path.abspath(reverse_video)}'\n")

        print(f"🔗 Склейка видео...")
        concat_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            output_video,
            '-y'
        ]
        subprocess.run(concat_cmd, check=True, capture_output=True)

        os.remove(reverse_video)
        os.remove(list_file)
        os.rmdir(temp_dir)

        print(f"✅ Готово! Результат: {output_video}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка FFmpeg: {e}")
        if e.stderr:
            print(f"Детали: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


def slow_down_video_simple(input_video, output_video, speed_factor=0.5):
    """
    Упрощенная версия замедления видео (без временной папки)

    Args:
        input_video: путь к исходному видео
        output_video: путь для сохранения результата
        speed_factor: коэффициент скорости (0.5 = в 2 раза медленнее)
    """
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
    create_reverse_with_fade(
        input_video="input_data/temp1.mp4",
        output_video="input_data/backv1.mp4"
    )
    slow_down_video_simple("input_data/backv1.mp4", "input_data/backv.mp4", speed_factor=1)