from io import BytesIO
from zipfile import ZipFile

from PIL import Image

from icon_processor import export_icons_zip, render_preview


def _sample_image() -> Image.Image:
    return Image.new("RGBA", (640, 400), (240, 90, 50, 255))


def test_render_preview_returns_png_bytes() -> None:
    preview = render_preview(_sample_image(), "rounded", 1.2, 0.15, -0.10)
    assert preview[:8] == b"\x89PNG\r\n\x1a\n"


def test_export_windows_zip_contains_ico_and_pngs() -> None:
    output = export_icons_zip(_sample_image(), "windows", "rounded", 0.9, 0.0, 0.0)

    with ZipFile(BytesIO(output), "r") as zf:
        names = set(zf.namelist())

    assert "icon.ico" in names
    assert "icon_1024.png" in names
    assert "icon_512.png" in names
    assert "icon_256.png" in names


def test_export_all_zip_contains_platform_folders() -> None:
    output = export_icons_zip(_sample_image(), "all", "circle", 1.35, -0.22, 0.18)

    with ZipFile(BytesIO(output), "r") as zf:
        names = set(zf.namelist())

    assert "windows/icon.ico" in names
    assert "windows/icon_512.png" in names
    assert "macos/icon_1024x1024.png" in names
    assert "ios/AppIcon-1024.png" in names
    assert "android/mipmap-xxxhdpi/ic_launcher.png" in names
