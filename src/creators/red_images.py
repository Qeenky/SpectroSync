import os
import shutil
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def blur_background_image(image_path, output_path, blur_type='gaussian', blur_radius=5):
    """
    Размытие фонового изображения

    blur_type: 'gaussian', 'box', 'min', 'max'
    """
    print(f"Замыливание фонового изображения (тип: {blur_type}, радиус: {blur_radius})...")

    img = Image.open(image_path).convert('RGBA')
    img = img.resize((1920, 1080))

    if blur_type == 'gaussian':
        blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    elif blur_type == 'box':
        blurred = img.filter(ImageFilter.BoxBlur(radius=blur_radius))
    elif blur_type == 'min':
        blurred = img.filter(ImageFilter.MinFilter(size=blur_radius))
    elif blur_type == 'max':
        blurred = img.filter(ImageFilter.MaxFilter(size=blur_radius))
    else:
        blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    blurred.convert('RGB').save(output_path, quality=95)

    print(f"Готово: {output_path}")
    return True


def add_gradient_fullscreen_image(image_path, output_path):
    print("Создание полноэкранного градиента...")

    img = Image.open(image_path).convert('RGBA')
    img = img.resize((1920, 1080))

    gradient = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    black_zone_start = 900

    print(f"  Градиент: Y=0-{black_zone_start}")
    print(f"  Черная зона: Y={black_zone_start}-1080")

    for y in range(0, black_zone_start):
        progress = y / black_zone_start
        alpha = int(255 * progress)
        draw.rectangle([(0, y), (1920, y)], fill=(0, 0, 0, alpha))

    for y in range(black_zone_start, 1080):
        draw.rectangle([(0, y), (1920, y)], fill=(0, 0, 0, 255))

    result = Image.alpha_composite(img, gradient)
    result.convert('RGB').save(output_path, quality=95)

    print(f"Готово: {output_path}")
    return True


def add_text_to_image(image_path, audio_path, output_path,
                      title_font_size=50, artist_font_size=50,
                      title_position=(600, 250), artist_position=(600, 310),
                      text_color=(255, 255, 255, 255),
                      stroke_width=2, stroke_color=(0, 0, 0, 255),
                      font_path=None):
    """
    Добавляет название трека и артиста на изображение
    """
    filename = os.path.splitext(os.path.basename(audio_path))[0]

    if ' - ' in filename:
        parts = filename.split(' - ', 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        title = filename
        artist = ""

    print(f"📝 Добавление текста на изображение...")
    print(f"   Название: {title}")
    print(f"   Артист: {artist}")

    img = Image.open(image_path).convert('RGBA')
    img = img.resize((1920, 1080))

    txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    try:
        if font_path and os.path.exists(font_path):
            title_font = ImageFont.truetype(font_path, title_font_size)
            artist_font = ImageFont.truetype(font_path, artist_font_size)
        else:
            try:
                title_font = ImageFont.truetype("arial.ttf", title_font_size)
                artist_font = ImageFont.truetype("arial.ttf", artist_font_size)
            except:
                title_font = ImageFont.load_default()
                artist_font = ImageFont.load_default()
    except:
        title_font = ImageFont.load_default()
        artist_font = ImageFont.load_default()

    def draw_text_with_stroke(draw, text, position, font, text_color, stroke_width, stroke_color):
        x, y = position

        if stroke_width > 0:
            for offset_x in range(-stroke_width, stroke_width + 1):
                for offset_y in range(-stroke_width, stroke_width + 1):
                    if offset_x != 0 or offset_y != 0:
                        draw.text(
                            (x + offset_x, y + offset_y),
                            text,
                            font=font,
                            fill=stroke_color
                        )

        draw.text((x, y), text, font=font, fill=text_color)

    if title:
        draw_text_with_stroke(
            draw, title, title_position, title_font,
            text_color, stroke_width, stroke_color
        )
    if artist:
        draw_text_with_stroke(
            draw, artist, artist_position, artist_font,
            text_color, stroke_width, stroke_color
        )

    result = Image.alpha_composite(img, txt_layer)
    result.convert('RGB').save(output_path, quality=95)

    print(f"✅ Готово: {output_path}")
    return True


def blur_video_background(video_path, output_path, blur_strength=5):
    """
    Размытие видео с помощью FFmpeg
    """
    print(f"🎬 Размытие видео (сила: {blur_strength})...")

    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f'boxblur={blur_strength}:1',
        '-c:a', 'copy',
        '-y',
        output_path
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Видео размыто: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при размытии видео: {e.stderr}")
        return False


def add_gradient_to_video(duration, output_mov_path, direction="bottom"):
    """
    Создает MOV видео с градиентом на прозрачном фоне (затемнение снизу вверх или сверху вниз)
    Градиент создается так же, как в add_gradient_fullscreen_image

    Args:
        duration: длительность видео в секундах
        output_mov_path: путь для сохранения MOV файла
        direction: направление градиента ("bottom" - снизу вверх, "top" - сверху вниз)

    Returns:
        bool: True если успешно, False если ошибка
    """

    print("🎬 Создание видео с градиентом на прозрачном фоне...")
    print(f"   Длительность: {duration} сек")
    print(f"   Направление: {direction}")

    temp_dir = tempfile.mkdtemp()
    frame_path = os.path.join(temp_dir, "gradient_frame.png")

    print("   Создание градиента...")

    gradient = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    black_zone_start = 900

    if direction == "bottom":
        print(f"   Параметры градиента (снизу вверх):")
        print(f"     - Градиент: Y=0-{black_zone_start}")
        print(f"     - Черная зона: Y={black_zone_start}-1080")

        for y in range(0, black_zone_start):
            progress = y / black_zone_start
            alpha = int(255 * progress)
            draw.rectangle([(0, y), (1920, y)], fill=(0, 0, 0, alpha))

        for y in range(black_zone_start, 1080):
            draw.rectangle([(0, y), (1920, y)], fill=(0, 0, 0, 255))

    elif direction == "top":
        # Градиент сверху вниз
        print(f"   Параметры градиента (сверху вниз):")
        print(f"     - Черная зона: Y=0-180")
        print(f"     - Градиент: Y=180-1080")

        black_zone_end = 180

        for y in range(0, black_zone_end):
            draw.rectangle([(0, y), (1920, y)], fill=(0, 0, 0, 255))

        for y in range(black_zone_end, 1080):
            progress = (y - black_zone_end) / (1080 - black_zone_end)
            alpha = int(255 * (1 - progress))
            draw.rectangle([(0, y), (1920, y)], fill=(0, 0, 0, alpha))

    else:
        print(f"❌ Неизвестное направление: {direction}. Используйте 'bottom' или 'top'")
        shutil.rmtree(temp_dir)
        return False

    gradient.save(frame_path, 'PNG')
    print(f"   Кадр с градиентом сохранен")
    print("   Конвертация в MOV с прозрачностью...")

    cmd = [
        'ffmpeg',
        '-loop', '1',
        '-i', frame_path,
        '-c:v', 'qtrle',
        '-pix_fmt', 'rgba',
        '-t', str(duration),
        '-y',
        output_mov_path
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Видео с градиентом создано: {output_mov_path}")

        file_size = os.path.getsize(output_mov_path) / (1024 * 1024)
        print(f"   Размер файла: {file_size:.2f} MB")
        shutil.rmtree(temp_dir)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при создании видео: {e.stderr}")
        shutil.rmtree(temp_dir)
        return False

def create_text_video(audio_path, output_mov_path,
                      title_font_size=70, artist_font_size=60,
                      text_color=(255, 255, 255, 255),
                      bg_color=(0, 0, 0, 0),
                      font_path=None,
                      start_x=600, start_y=250):
    """
    Создает MOV видео с текстом на прозрачном фоне для последующего наложения

    Args:
        audio_path: путь к аудио файлу (из названия парсится "исполнитель - название")
        output_mov_path: путь для сохранения MOV файла
        title_font_size: размер шрифта для названия
        artist_font_size: размер шрифта для исполнителя
        text_color: цвет текста (R, G, B, A)
        bg_color: цвет фона под текстом (R, G, B, A)
        padding: отступ фона вокруг текста
        font_path: путь к шрифту (если None, используется дефолтный)
        start_x: начальная координата X для текста
        start_y: начальная координата Y для текста

    Returns:
        bool: True если успешно, False если ошибка
    """

    filename = os.path.splitext(os.path.basename(audio_path))[0]

    if ' - ' in filename:
        parts = filename.split(' - ', 1)
        artist = parts[0].strip()
        title = parts[1].strip()
    else:
        title = filename
        artist = ""

    print(f"🎬 Создание видео с текстом...")
    print(f"   Исполнитель: {artist}")
    print(f"   Название: {title}")
    print(f"   Позиция: ({start_x}, {start_y})")
    print(f"   Размер видео: 1920x1080")
    print(f"   Выходной файл: {output_mov_path}")

    duration_cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]

    try:
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        duration_str = str(int(duration)) + "." + str(int((duration % 1) * 1000))
        print(f"   Длительность: {duration} сек")
    except Exception as e:
        print(f"⚠️ Ошибка получения длительности: {e}")
        duration = 10.0
        print(f"⚠️ Использую {duration} сек")

    temp_dir = tempfile.mkdtemp()
    frame_path = os.path.join(temp_dir, "frame.png")

    try:
        if font_path and os.path.exists(font_path):
            title_font = ImageFont.truetype(font_path, title_font_size)
            artist_font = ImageFont.truetype(font_path, artist_font_size)
        else:
            try:
                title_font = ImageFont.truetype("arial.ttf", title_font_size)
                artist_font = ImageFont.truetype("arial.ttf", artist_font_size)
            except:
                print("⚠️ Шрифт не найден, использую дефолтный")
                title_font = ImageFont.load_default()
                artist_font = ImageFont.load_default()
    except Exception as e:
        print(f"⚠️ Ошибка загрузки шрифта: {e}")
        title_font = ImageFont.load_default()
        artist_font = ImageFont.load_default()

    img = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))  # Полностью прозрачный фон
    draw = ImageDraw.Draw(img)

    def draw_text_with_bg(draw, text, x, y, font, text_color, bg_color):
        """Рисует текст с фоном в указанной позиции"""
        if not text:
            return 0, 0

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        draw.rectangle(
            [
                x,
                y,
                x + text_width,
                y + text_height
            ],
            fill=bg_color
        )
        draw.text((x, y), text, font=font, fill=text_color)

        return text_width, text_height

    if artist and title:
        current_x = start_x
        current_y = start_y

        title_width, title_height = draw_text_with_bg(
            draw, title, current_x, current_y,
            title_font, text_color, bg_color
        )

        artist_y = current_y + title_height + 10
        draw_text_with_bg(
            draw, artist, current_x, artist_y,
            artist_font, text_color, bg_color
        )
    elif title:
        draw_text_with_bg(
            draw, title, start_x, start_y,
            title_font, text_color, bg_color
        )

    img.save(frame_path, 'PNG')
    print(f"✅ Кадр создан: {frame_path}")
    print("🎬 Конвертация в MOV с прозрачностью...")

    cmd = [
        'ffmpeg',
        '-loop', '1',
        '-i', frame_path,
        '-c:v', 'qtrle',  # Кодек Apple Animation для прозрачности
        '-pix_fmt', 'rgba',
        '-t', str(duration),
        '-y',
        output_mov_path
    ]

    try:
        # Запускаем FFmpeg и показываем прогресс
        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Видео с текстом создано: {output_mov_path}")

        # Проверяем размер файла
        file_size = os.path.getsize(output_mov_path) / (1024 * 1024)
        print(f"   Размер файла: {file_size:.2f} MB")

        # Очищаем временные файлы
        shutil.rmtree(temp_dir)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при создании видео: {e.stderr}")