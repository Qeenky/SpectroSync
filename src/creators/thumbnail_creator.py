import os
import subprocess

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FFMpegWriter
from PIL import Image


def create_thumbnail_bar_video(thumbnail_path, output_video, audio_path, fps=30, dpi=150):
    """
    Создаёт видео с тумбой слева и горизонтальным прогресс-баром справа

    Размер видео: 1000x400 пикселей
    - Слева: тумба 400x400
    - Справа: область 600x400 с горизонтальным баром и временем
    - Бар: 560x8 (с отступами для текста времени)
    - Под баром: прошедшее время (слева) и оставшееся время (справа)
    """
    filename = os.path.splitext(os.path.basename(audio_path))[0]

    if ' - ' in filename:
        parts = filename.split(' - ', 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        title = filename
        artist = ""

    # Получаем длительность аудио
    duration_cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]

    try:
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        audio_duration = float(result.stdout.strip())
    except Exception as e:
        print(f"Ошибка получения длительности: {e}")
        audio_duration = 180

    width_px = 1000
    height_px = 400

    # Позиции элементов
    thumb_x = 0
    thumb_width = 400
    thumb_height = 400

    bar_area_x = 400
    bar_area_width = 600
    bar_area_height = 400

    # Параметры бара
    bar_width = 560
    bar_height = 8
    bar_x = bar_area_x + (bar_area_width - bar_width) // 2
    bar_y = 200

    figsize_width = width_px / dpi
    figsize_height = height_px / dpi

    fig, ax = plt.subplots(figsize=(figsize_width, figsize_height), facecolor='none', dpi=dpi)
    ax.set_facecolor('none')

    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)

    ax.set_xlim(0, width_px)
    ax.set_ylim(height_px, 0)

    # Загружаем и отображаем тумбу слева
    thumb_img = Image.open(thumbnail_path)
    thumb_img = thumb_img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)

    ax.imshow(thumb_img, extent=[thumb_x, thumb_x + thumb_width, thumb_height, 0],
              aspect='auto', zorder=1)

    # Серый фон для прогресс-бара
    gray_bar = plt.Rectangle(
        (bar_x, bar_y), bar_width, bar_height,
        facecolor='gray', alpha=0.5, linewidth=0, zorder=2
    )
    ax.add_patch(gray_bar)

    # Оранжевый прогресс-бар
    # TODO: сделать зависимым от фона
    orange_bar = plt.Rectangle(
        (bar_x, bar_y), 0, bar_height,
        facecolor='orange', alpha=0.8, linewidth=0, zorder=3
    )
    ax.add_patch(orange_bar)

    def format_time(seconds):
        """Форматирует время в MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    time_elapsed_text = ax.text(
        bar_x, bar_y + 20,
        '00:00',
        color='white', fontsize=11, fontweight='bold',
        ha='left', va='top', zorder=4
    )

    time_remaining_text = ax.text(
        bar_x + bar_width, bar_y + 20,
        format_time(audio_duration),
        color='white', fontsize=11, fontweight='bold',
        ha='right', va='top', zorder=4
    )

    display_text = f'{artist} - {title}' if artist else title
    if len(display_text) > 60:
        display_text = display_text[:37] + "..."

    title_text = ax.text(
        bar_x + bar_width / 2, bar_y - 15,
        display_text,
        color='white', fontsize=8, fontweight='normal',
        ha='center', va='bottom', zorder=4
    )

    ax.axis('off')
    ax.set_aspect('equal')

    def update(frame):
        time_sec = frame / fps
        progress = min(time_sec / audio_duration, 1.0)

        orange_bar.set_width(bar_width * progress)
        time_elapsed_text.set_text(format_time(time_sec))
        time_remaining_text.set_text(format_time(max(0, audio_duration - time_sec)))

        return [orange_bar, time_elapsed_text, time_remaining_text]

    total_frames = int(audio_duration * fps)
    ani = animation.FuncAnimation(
        fig, update, frames=total_frames,
        interval=1000 / fps, blit=True
    )

    writer = FFMpegWriter(
        fps=fps,
        metadata=dict(artist='SpectroSync'),
        codec='png',
        extra_args=[
            '-pix_fmt', 'rgba',
            '-vcodec', 'png',
            '-compression_level', '1'
        ]
    )

    print(f"🎬 Создание видео с тумбой и горизонтальным баром справа...")
    print(f"📐 Размер видео: {width_px}x{height_px}")
    print(f"🖼️ Тумба: 400x400 (слева)")
    print(f"📊 Бар: {bar_width}x{bar_height} (в правой части 600px)")
    print(f"⏱️ Длительность: {audio_duration:.0f} сек")
    print(f"📝 Текст: {display_text}")

    ani.save(output_video, writer=writer, dpi=dpi,
             savefig_kwargs={'transparent': True, 'bbox_inches': 'tight', 'pad_inches': 0})
    plt.close()

    print(f"✅ Готово: {output_video}")
    return True