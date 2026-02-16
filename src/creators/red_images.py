from PIL import Image, ImageDraw


def add_gradient_fullscreen(image_path, output_path):
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

