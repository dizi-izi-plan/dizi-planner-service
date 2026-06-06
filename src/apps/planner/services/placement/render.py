"""Отрисовка результата раскладки в SVG и PNG.

Портировано из algorithm_v2 (dizi-izi-backend): функции принимают
экземпляр :class:`Core` после ``run_algorithm()`` и возвращают
готовый артефакт (строку SVG / байты PNG), не записывая на диск.

Система координат алгоритма: ось Y растёт вверх, начало — в левом
нижнем углу комнаты. В SVG/растре Y растёт вниз, поэтому координаты
переворачиваются по вертикали.
"""

from io import BytesIO
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


def render_to_svg(core, scale: float = 1, margin: int = 50) -> str:
    """Рендерит раскладку в SVG-строку."""
    room = core.room
    width = room.width * scale + margin * 2
    height = room.length * scale + margin * 2

    def points(corners):
        return " ".join(f"{c.x * scale + margin:.2f},{c.y * scale + margin:.2f}" for c in corners)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'font-family="sans-serif" font-size="12">',
        # Переворот оси Y: вверх в алгоритме -> вниз в SVG
        f'<g transform="translate(0,{height}) scale(1,-1)">',
        f'<rect x="{margin}" y="{margin}" width="{room.width * scale}" '
        f'height="{room.length * scale}" fill="#e6e6e6" stroke="black" stroke-width="2"/>',
    ]

    for zone in core.get_zones or []:
        parts.append(
            f'<polygon points="{points(zone.get_corners())}" '
            f'fill="lightblue" fill-opacity="0.3" stroke="steelblue"/>'
        )

    for obj in room.furnitures:
        color = "lightgreen" if obj.dimension == "large_furniture" else "#ffff99"
        parts.append(
            f'<polygon points="{points(obj.get_corners())}" fill="{color}" stroke="black"/>'
        )

    for opening in core.get_openings:
        color = "skyblue" if opening.name == "окно" else "cornflowerblue"
        parts.append(
            f'<polygon points="{points(opening.get_corners())}" fill="{color}" stroke="darkblue"/>'
        )

    for point in room.electricity_points:
        cx = point.center.x * scale + margin
        cy = point.center.y * scale + margin
        parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="4" fill="red" stroke="darkred"/>')

    parts.append("</g>")

    # Подписи рисуем поверх (без флипа), иначе текст будет вверх ногами
    for obj in room.furnitures:
        cx = obj.center.x * scale + margin
        cy = (room.length - obj.center.y) * scale + margin
        parts.append(
            f'<text x="{cx:.2f}" y="{cy:.2f}" text-anchor="middle" '
            f'dominant-baseline="middle" fill="black">{escape(obj.name)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def render_to_png(core, scale: float = 1, margin: int = 50) -> bytes:
    """Рендерит раскладку в PNG-байты."""
    room = core.room
    width = int(room.width * scale + margin * 2)
    height = int(room.length * scale + margin * 2)
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img, "RGBA")

    def to_px(x, y):
        return (x * scale + margin, (room.length - y) * scale + margin)

    def poly(corners):
        return [to_px(c.x, c.y) for c in corners]

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
    except OSError:
        font = ImageFont.load_default()

    draw.rectangle(
        [to_px(0, room.length), to_px(room.width, 0)],
        outline="black",
        fill=(230, 230, 230),
        width=2,
    )

    for zone in core.get_zones or []:
        draw.polygon(poly(zone.get_corners()), fill=(173, 216, 230, 80), outline=(70, 130, 180))

    for obj in room.furnitures:
        color = (144, 238, 144) if obj.dimension == "large_furniture" else (255, 255, 153)
        draw.polygon(poly(obj.get_corners()), fill=color, outline="black")
        cx, cy = to_px(obj.center.x, obj.center.y)
        draw.text((cx, cy), obj.name, fill="black", anchor="mm", font=font)

    for opening in core.get_openings:
        color = (135, 206, 235) if opening.name == "окно" else (100, 149, 237)
        draw.polygon(poly(opening.get_corners()), fill=color, outline=(0, 0, 139))

    for point in room.electricity_points:
        ex, ey = to_px(point.center.x, point.center.y)
        r = 4
        draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill="red", outline="darkred")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
