import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FFMpegWriter
from PIL import Image


def create_thumbnail_bar_video(thumbnail_path, output_video, audio_duration, fps=30, dpi=150):
    """
    Создаёт видео с тумбой и прогресс-баром на прозрачном фоне

    Размер видео: 400x410 пикселей
    - Тумба: 400x400 (вверху)
    - Отступ: 2px между тумбой и баром
    - Бар: 400x8 (внизу)

    Args:
        thumbnail_path: путь к изображению тумбы
        output_video: путь для сохранения видео
        audio_duration: длительность видео в секундах
        fps: кадров в секунду
        dpi: разрешение для matplotlib
    """
    width_px = 400
    height_px = 410

    thumb_y = 0
    bar_y = 402

    figsize_width = width_px / dpi
    figsize_height = height_px / dpi

    fig, ax = plt.subplots(figsize=(figsize_width, figsize_height), facecolor='none', dpi=dpi)
    ax.set_facecolor('none')

    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)

    ax.set_xlim(0, width_px)
    ax.set_ylim(height_px, 0)

    thumb_img = Image.open(thumbnail_path)
    thumb_img = thumb_img.resize((400, 400), Image.Resampling.LANCZOS)

    ax.imshow(thumb_img, extent=[0, width_px, thumb_y + 400, thumb_y],
              aspect='auto', zorder=1)

    gray_bar = plt.Rectangle(
        (0, bar_y), width_px, 8,
        facecolor='gray', alpha=0.5, linewidth=0, zorder=2
    )
    ax.add_patch(gray_bar)

    orange_bar = plt.Rectangle(
        (0, bar_y), 0, 8,
        facecolor='orange', alpha=0.8, linewidth=0, zorder=3
    )
    ax.add_patch(orange_bar)
    ax.axis('off')

    ax.set_aspect('equal')

    def update(frame):
        time_sec = frame / fps
        progress = min(time_sec / audio_duration, 1.0)

        orange_bar.set_width(width_px * progress)

        return [orange_bar]

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

    print(f"🎬 Создание видео с тумбой и баром...")
    print(f"📐 Размер видео: {width_px}x{height_px}")
    print(f"🖼️ Тумба: 400x400 (y=0)")
    print(f"⬜ Отступ: 2px")
    print(f"📊 Бар: 400x8 (y=402)")
    print(f"⏱️ Длительность: {audio_duration} сек")

    ani.save(output_video, writer=writer, dpi=dpi,
             savefig_kwargs={'transparent': True, 'bbox_inches': 'tight', 'pad_inches': 0})
    plt.close()

    print(f"✅ Готово: {output_video}")
    return True