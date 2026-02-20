import subprocess


def create_thumbnail_bar_video(input_video, thumbnail_path, output_video, audio_duration):
    cmd = [
        'ffmpeg',
        '-i', input_video,
        '-i', thumbnail_path,
        '-filter_complex',
        f'[1:v]scale=400:400[thumb]; '
        f'[0:v][thumb]overlay=200:250[v0]; '
        f'[v0]drawbox=200:700:600:8:gray@0.5:t=fill[v1]; '
        f'[v1]drawbox=200:700:600*t/{float(audio_duration)}:8:orange@0.8:t=fill[out]',
        '-map', '[out]',
        '-map', '0:a',
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '23',
        '-c:a', 'copy',
        '-y',
        output_video
    ]

    print(f"🖼️ Добавление тумбы и бара...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Готово: {output_video}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e.stderr}")
        return False