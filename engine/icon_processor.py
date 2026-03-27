from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image, ImageDraw

Platform = str
Frame = str

PLATFORMS: Dict[str, List[Tuple[str, int]]] = {
    "windows": [("icon", 256), ("icon", 128), ("icon", 64), ("icon", 32), ("icon", 16)],
    "macos": [("icon_1024x1024", 1024), ("icon_512x512", 512), ("icon_256x256", 256), ("icon_128x128", 128)],
    "ios": [("AppIcon-1024", 1024), ("AppIcon-180", 180), ("AppIcon-120", 120), ("AppIcon-87", 87), ("AppIcon-60", 60)],
    "android": [("mipmap-xxxhdpi/ic_launcher", 192), ("mipmap-xxhdpi/ic_launcher", 144), ("mipmap-xhdpi/ic_launcher", 96), ("mipmap-hdpi/ic_launcher", 72), ("mipmap-mdpi/ic_launcher", 48)],
}

WINDOWS_ICO_SIZES: List[int] = [256, 128, 64, 32, 16]
WINDOWS_EXTRA_PNG_SIZES: List[int] = [1024, 512, 256, 128, 64, 48, 32, 16]


def open_image_rgba(image_path: str | Path) -> Image.Image:
    img = Image.open(image_path)
    return img.convert("RGBA")


def square_canvas(img: Image.Image, size: int, zoom: float, move_x: float, move_y: float) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    src = img.copy()

    base_scale = min(size / max(src.width, 1), size / max(src.height, 1))
    clamped_zoom = max(0.1, min(8.0, zoom))
    final_scale = base_scale * clamped_zoom

    new_w = max(1, int(src.width * final_scale))
    new_h = max(1, int(src.height * final_scale))
    src = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    shift_x = int(max(-1.0, min(1.0, move_x)) * size * 0.5)
    shift_y = int(max(-1.0, min(1.0, move_y)) * size * 0.5)

    x = (size - src.width) // 2 + shift_x
    y = (size - src.height) // 2 + shift_y

    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    layer.paste(src, (x, y), src)
    canvas.alpha_composite(layer)
    return canvas


def apply_frame(img: Image.Image, frame: Frame) -> Image.Image:
    w, h = img.size
    if w != h:
        size = min(w, h)
        left = (w - size) // 2
        top = (h - size) // 2
        img = img.crop((left, top, left + size, top + size))
        w, h = img.size

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)

    if frame == "circle":
        draw.ellipse((0, 0, w - 1, h - 1), fill=255)
    elif frame == "rounded":
        radius = int(w * 0.22)
        draw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    else:
        draw.rectangle((0, 0, w - 1, h - 1), fill=255)

    out = img.copy()
    out.putalpha(mask)
    return out


def build_icon(img: Image.Image, size: int, frame: Frame, zoom: float, move_x: float, move_y: float) -> Image.Image:
    squared = square_canvas(img, size, zoom, move_x, move_y)
    return apply_frame(squared, frame)


def iter_platform_targets(platform: Platform) -> Iterable[Tuple[str, int]]:
    if platform == "all":
        for key in ["windows", "macos", "ios", "android"]:
            for item in PLATFORMS[key]:
                yield f"{key}/{item[0]}", item[1]
        return

    if platform not in PLATFORMS:
        raise ValueError("Plataforma no soportada")

    for name, size in PLATFORMS[platform]:
        yield name, size


def render_preview(img: Image.Image, frame: Frame, zoom: float, move_x: float, move_y: float, size: int = 512) -> bytes:
    icon = build_icon(img, size, frame, zoom, move_x, move_y)
    out = BytesIO()
    icon.save(out, format="PNG")
    return out.getvalue()


def export_icons_zip(img: Image.Image, platform: Platform, frame: Frame, zoom: float, move_x: float, move_y: float) -> bytes:
    zip_buf = BytesIO()

    with ZipFile(zip_buf, "w", compression=ZIP_DEFLATED) as zf:
        if platform in {"windows", "all"}:
            ico_images = [build_icon(img, s, frame, zoom, move_x, move_y) for s in WINDOWS_ICO_SIZES]
            ico_buf = BytesIO()
            ico_images[0].save(ico_buf, format="ICO", sizes=[(s, s) for s in WINDOWS_ICO_SIZES])
            ico_base = "windows/icon.ico" if platform == "all" else "icon.ico"
            zf.writestr(ico_base, ico_buf.getvalue())

            for png_size in WINDOWS_EXTRA_PNG_SIZES:
                png_icon = build_icon(img, png_size, frame, zoom, move_x, move_y)
                png_buf = BytesIO()
                png_icon.save(png_buf, format="PNG")
                png_name = f"icon_{png_size}.png"
                png_path = f"windows/{png_name}" if platform == "all" else png_name
                zf.writestr(png_path, png_buf.getvalue())

        for name, size in iter_platform_targets(platform):
            if platform == "windows" or name.startswith("windows/"):
                continue

            icon = build_icon(img, size, frame, zoom, move_x, move_y)
            png_buf = BytesIO()
            icon.save(png_buf, format="PNG")
            file_path = f"{name}.png"
            if platform != "all" and "/" not in file_path:
                file_path = f"{platform}/{file_path}"
            zf.writestr(file_path, png_buf.getvalue())

    return zip_buf.getvalue()
