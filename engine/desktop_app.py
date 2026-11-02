from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from PyQt5.QtCore import QRectF, Qt, QTimer
from PyQt5.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QFont,
    QIcon,
    QImage,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import Theme, setTheme, setThemeColor

from icon_processor import export_icons_zip, open_image_rgba, render_preview
from version import __version__

def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]


ROOT = _project_root()
ASSETS_DIR = ROOT / "assets"
APP_ICON_PNG = ASSETS_DIR / "app_icon.png"
APP_ICON_ICO = ASSETS_DIR / "app_icon.ico"

ACCENT = "#7C5CFF"
SURFACE = "#171A22"
PLATFORMS = [
    ("all", "Todas"),
    ("windows", "Windows"),
    ("macos", "macOS"),
    ("ios", "iOS"),
    ("android", "Android"),
]
FRAMES = [
    ("rounded", "▢"),
    ("circle", "○"),
    ("square", "□"),
]
IMAGE_FILTER = "Imágenes (*.png *.jpg *.jpeg *.webp)"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class PreviewCanvas(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._pixmap = QPixmap()
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_preview(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#12141A"))

        inset = 36
        window = QRectF(self.rect().adjusted(inset, inset, -inset, -inset))
        if window.width() < 180 or window.height() < 160:
            window = QRectF(self.rect().adjusted(12, 12, -12, -12))

        shadow = window.adjusted(0, 6, 0, 8)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 70))
        painter.drawRoundedRect(shadow, 14, 14)

        painter.setBrush(QColor("#232838"))
        painter.drawRoundedRect(window, 14, 14)

        bar = QRectF(window.left(), window.top(), window.width(), 34)
        bar_path = QPainterPath()
        bar_path.addRoundedRect(window, 14, 14)
        painter.setClipPath(bar_path)
        painter.setBrush(QColor("#1A1E2B"))
        painter.drawRect(bar)
        painter.setClipping(False)

        colors = ("#FF5F57", "#FEBC2E", "#28C840")
        for index, color in enumerate(colors):
            painter.setBrush(QColor(color))
            painter.drawEllipse(QRectF(window.left() + 14 + index * 16, window.top() + 12, 9, 9))

        content = QRectF(window.left(), window.top() + 34, window.width(), window.height() - 34)
        if self._pixmap.isNull():
            return

        max_side = int(min(content.width(), content.height()) * 0.62)
        scaled = self._pixmap.scaled(max_side, max_side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = int(content.center().x() - scaled.width() / 2)
        y = int(content.center().y() - scaled.height() / 2)
        painter.drawPixmap(x, y, scaled)


class SizeChip(QLabel):
    def __init__(self, size: int) -> None:
        super().__init__()
        self.size_px = size
        self.setFixedSize(52, 52)
        self.setAlignment(Qt.AlignCenter)
        self.setObjectName("sizeChip")

    def set_preview(self, pixmap: QPixmap) -> None:
        if pixmap.isNull():
            self.clear()
            return
        shown = min(self.size_px, 44)
        scaled = pixmap.scaled(shown, shown, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        canvas = QPixmap(52, 52)
        canvas.fill(QColor(SURFACE))
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap((52 - scaled.width()) // 2, (52 - scaled.height()) // 2, scaled)
        painter.end()
        self.setPixmap(canvas)


class IconWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ICON")
        self.resize(980, 620)
        self.setMinimumSize(860, 540)
        self.setAcceptDrops(True)
        self.image_path: Path | None = None
        self.source_image: Image.Image | None = None
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)

        self.canvas = PreviewCanvas()
        self.size_chips = [SizeChip(size) for size in (128, 64, 32, 16)]

        self.zoom_slider = self._slider(50, 300, 100)
        self.zoom_spin = self._spin(0.50, 3.00, 1.00)
        self.move_x_slider = self._slider(-100, 100, 0)
        self.move_x_spin = self._spin(-1.00, 1.00, 0.00)
        self.move_y_slider = self._slider(-100, 100, 0)
        self.move_y_spin = self._spin(-1.00, 1.00, 0.00)

        self.platform_group = QButtonGroup(self)
        self.platform_group.setExclusive(True)
        self.frame_group = QButtonGroup(self)
        self.frame_group.setExclusive(True)

        self._build_ui()
        self._wire_events()
        self._apply_theme()
        self._apply_window_icon()

    def _slider(self, minimum: int, maximum: int, value: int) -> QSlider:
        slider = QSlider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        slider.setObjectName("studioSlider")
        return slider

    def _spin(self, minimum: float, maximum: float, value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSingleStep(0.01)
        spin.setDecimals(2)
        spin.setAccelerated(True)
        spin.setValue(value)
        spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        spin.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        spin.setFixedWidth(54)
        spin.setFocusPolicy(Qt.NoFocus)
        return spin

    def _chip(self, text: str, value: str, group: QButtonGroup, checked: bool = False) -> QPushButton:
        button = QPushButton(text)
        button.setCheckable(True)
        button.setChecked(checked)
        button.setProperty("value", value)
        button.setObjectName("chip")
        button.setCursor(Qt.PointingHandCursor)
        group.addButton(button)
        return button

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(300)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(4, 4, 8, 4)
        side.setSpacing(10)

        brand = QHBoxLayout()
        brand.setSpacing(8)
        mark = QLabel()
        mark.setFixedSize(64, 64)
        if APP_ICON_PNG.exists():
            mark.setPixmap(QPixmap(str(APP_ICON_PNG)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.open_button = QPushButton("Abrir")
        self.open_button.setObjectName("ghost")
        self.open_button.setCursor(Qt.PointingHandCursor)
        brand.addWidget(mark)
        brand.addStretch(1)
        brand.addWidget(self.open_button)
        side.addLayout(brand)

        platforms = QHBoxLayout()
        platforms.setSpacing(6)
        for index, (value, label) in enumerate(PLATFORMS):
            platforms.addWidget(self._chip(label, value, self.platform_group, checked=index == 0))
        side.addLayout(platforms)

        frames = QHBoxLayout()
        frames.setSpacing(8)
        for index, (value, label) in enumerate(FRAMES):
            button = self._chip(label, value, self.frame_group, checked=index == 0)
            button.setObjectName("shape")
            button.setFixedHeight(32)
            frames.addWidget(button)
        side.addLayout(frames)

        side.addLayout(self._slider_row("Zoom", self.zoom_slider, self.zoom_spin, self.nudge_zoom_minus, self.nudge_zoom_plus))
        side.addLayout(self._slider_row("X", self.move_x_slider, self.move_x_spin, self.nudge_move_x_minus, self.nudge_move_x_plus))
        side.addLayout(self._slider_row("Y", self.move_y_slider, self.move_y_spin, self.nudge_move_y_minus, self.nudge_move_y_plus))

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.reset_button = QPushButton("Reiniciar")
        self.reset_button.setObjectName("ghost")
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.export_button = QPushButton("Exportar")
        self.export_button.setObjectName("primary")
        self.export_button.setCursor(Qt.PointingHandCursor)
        for button in (self.reset_button, self.export_button):
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumHeight(32)
        actions.addWidget(self.reset_button, 1)
        actions.addWidget(self.export_button, 1)
        side.addLayout(actions)
        side.addStretch(1)
        credit = QLabel("By chesterchasis")
        credit.setObjectName("credit")
        credit.setAlignment(Qt.AlignCenter)
        version_label = QLabel(__version__)
        version_label.setObjectName("credit")
        version_label.setAlignment(Qt.AlignCenter)
        side.addWidget(credit)
        side.addWidget(version_label)

        stage = QFrame()
        stage.setObjectName("stage")
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(8, 8, 8, 8)
        stage_layout.setSpacing(8)
        stage_layout.addWidget(self.canvas, 1)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        chips_row.addStretch(1)
        for chip in self.size_chips:
            chips_row.addWidget(chip)
        chips_row.addStretch(1)
        stage_layout.addLayout(chips_row)

        layout.addWidget(sidebar)
        layout.addWidget(stage, 1)

    def _slider_row(self, label_text: str, slider: QSlider, spin: QDoubleSpinBox, minus_cb, plus_cb) -> QVBoxLayout:
        wrapper = QVBoxLayout()
        wrapper.setSpacing(0)
        wrapper.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        minus_button = QPushButton("−")
        plus_button = QPushButton("+")
        for button, callback in ((minus_button, minus_cb), (plus_button, plus_cb)):
            button.setObjectName("stepper")
            button.setFixedSize(22, 22)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(callback)
        top.addWidget(label)
        top.addStretch(1)
        top.addWidget(minus_button)
        top.addWidget(spin)
        top.addWidget(plus_button)
        wrapper.addLayout(top)
        wrapper.addWidget(slider)
        return wrapper

    def _wire_events(self) -> None:
        self.open_button.clicked.connect(self.select_image)
        self.reset_button.clicked.connect(self.reset_adjustments)
        self.export_button.clicked.connect(self.export_zip)
        self.platform_group.buttonClicked.connect(self.schedule_preview)
        self.frame_group.buttonClicked.connect(self.schedule_preview)

        self.zoom_slider.valueChanged.connect(lambda value: self._sync_slider_to_spin(self.zoom_spin, value / 100.0))
        self.move_x_slider.valueChanged.connect(lambda value: self._sync_slider_to_spin(self.move_x_spin, value / 100.0))
        self.move_y_slider.valueChanged.connect(lambda value: self._sync_slider_to_spin(self.move_y_spin, value / 100.0))
        self.zoom_spin.valueChanged.connect(lambda value: self._sync_spin_to_slider(self.zoom_slider, value * 100))
        self.move_x_spin.valueChanged.connect(lambda value: self._sync_spin_to_slider(self.move_x_slider, value * 100))
        self.move_y_spin.valueChanged.connect(lambda value: self._sync_spin_to_slider(self.move_y_slider, value * 100))

    def _sync_slider_to_spin(self, spin: QDoubleSpinBox, value: float) -> None:
        if abs(spin.value() - value) > 0.001:
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        self.schedule_preview()

    def _sync_spin_to_slider(self, slider: QSlider, value: float) -> None:
        int_value = int(round(value))
        if slider.value() != int_value:
            slider.blockSignals(True)
            slider.setValue(int_value)
            slider.blockSignals(False)
        self.schedule_preview()

    def _apply_window_icon(self) -> None:
        icon_path = APP_ICON_ICO if APP_ICON_ICO.exists() else APP_ICON_PNG
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _apply_theme(self) -> None:
        setTheme(Theme.DARK)
        setThemeColor(QColor(ACCENT))
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background: {SURFACE};
                color: #E8ECF5;
                font-size: 13px;
                border: none;
            }}
            QFrame#sidebar {{
                background: {SURFACE};
                border: none;
            }}
            QFrame#stage {{
                background: #12141A;
                border: none;
                border-radius: 12px;
            }}
            QLabel#credit {{
                background: transparent;
                color: rgba(255, 255, 255, 150);
                border: none;
                font-size: 10px;
            }}
            QLabel#fieldLabel {{
                background: transparent;
                color: #9CA3AF;
                border: none;
                font-size: 12px;
            }}
            QLabel#sizeChip {{
                background: {SURFACE};
                border: none;
            }}
            QPushButton#chip, QPushButton#shape {{
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px 6px;
                min-height: 26px;
                color: #C5CAD6;
            }}
            QPushButton#chip:checked, QPushButton#shape:checked {{
                background: {ACCENT};
                color: #FFFFFF;
            }}
            QPushButton#ghost {{
                background: #222632;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                min-height: 30px;
                color: #E8ECF5;
            }}
            QPushButton#primary {{
                background: {ACCENT};
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                min-height: 30px;
                color: #FFFFFF;
                font-weight: 600;
            }}
            QPushButton#stepper {{
                background: transparent;
                border: none;
                color: #C5CAD6;
            }}
            QDoubleSpinBox {{
                background: transparent;
                border: none;
                color: #9CA3AF;
                padding: 0;
            }}
            QSlider#studioSlider {{
                background: transparent;
            }}
            QSlider#studioSlider::groove:horizontal {{
                height: 4px;
                background: #2A3142;
                border: none;
                border-radius: 2px;
            }}
            QSlider#studioSlider::handle:horizontal {{
                width: 14px;
                height: 14px;
                margin: -5px 0;
                background: {ACCENT};
                border: none;
                border-radius: 7px;
            }}
            QSlider#studioSlider::sub-page:horizontal {{
                background: {ACCENT};
                border: none;
                border-radius: 2px;
            }}
            """
        )

    def _selected_value(self, group: QButtonGroup, fallback: str) -> str:
        button = group.checkedButton()
        if button is None:
            return fallback
        return str(button.property("value"))

    def current_frame(self) -> str:
        return self._selected_value(self.frame_group, "rounded")

    def current_platform(self) -> str:
        return self._selected_value(self.platform_group, "all")

    def current_zoom(self) -> float:
        return self.zoom_spin.value()

    def current_move_x(self) -> float:
        return self.move_x_spin.value()

    def current_move_y(self) -> float:
        return self.move_y_spin.value()

    def nudge_zoom_minus(self) -> None:
        self.zoom_spin.setValue(max(0.5, self.zoom_spin.value() - 0.01))

    def nudge_zoom_plus(self) -> None:
        self.zoom_spin.setValue(min(3.0, self.zoom_spin.value() + 0.01))

    def nudge_move_x_minus(self) -> None:
        self.move_x_spin.setValue(max(-1.0, self.move_x_spin.value() - 0.01))

    def nudge_move_x_plus(self) -> None:
        self.move_x_spin.setValue(min(1.0, self.move_x_spin.value() + 0.01))

    def nudge_move_y_minus(self) -> None:
        self.move_y_spin.setValue(max(-1.0, self.move_y_spin.value() - 0.01))

    def nudge_move_y_plus(self) -> None:
        self.move_y_spin.setValue(min(1.0, self.move_y_spin.value() + 0.01))

    def reset_adjustments(self) -> None:
        self.zoom_spin.setValue(1.0)
        self.move_x_spin.setValue(0.0)
        self.move_y_spin.setValue(0.0)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if self._path_from_mime(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        path = self._path_from_mime(event)
        if path:
            self.load_image(path)
            event.acceptProposedAction()

    def _path_from_mime(self, event) -> Path | None:
        urls = event.mimeData().urls() if event.mimeData() else []
        if not urls:
            return None
        path = Path(urls[0].toLocalFile())
        if path.suffix.lower() in IMAGE_SUFFIXES:
            return path
        return None

    def select_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecciona una imagen", str(Path.home()), IMAGE_FILTER)
        if file_path:
            self.load_image(Path(file_path))

    def load_image(self, path: Path) -> None:
        self.image_path = path
        self.source_image = open_image_rgba(path)
        self.open_button.setText(path.stem[:18])
        self.schedule_preview()

    def schedule_preview(self) -> None:
        if self.source_image is None:
            return
        self.preview_timer.start(120)

    def update_preview(self) -> None:
        if self.source_image is None:
            return
        png_bytes = render_preview(
            self.source_image,
            self.current_frame(),
            self.current_zoom(),
            self.current_move_x(),
            self.current_move_y(),
            size=640,
        )
        image = QImage.fromData(png_bytes, "PNG")
        pixmap = QPixmap.fromImage(image)
        self.canvas.set_preview(pixmap)
        for chip in self.size_chips:
            chip.set_preview(pixmap)

    def export_zip(self) -> None:
        if self.source_image is None:
            QMessageBox.warning(self, "ICON", "Abre una imagen primero.")
            return

        suggested = Path.home() / "ICON-export.zip"
        output_path, _ = QFileDialog.getSaveFileName(self, "Guardar ZIP", str(suggested), "ZIP (*.zip)")
        if not output_path:
            return

        zip_bytes = export_icons_zip(
            self.source_image,
            self.current_platform(),
            self.current_frame(),
            self.current_zoom(),
            self.current_move_x(),
            self.current_move_y(),
        )
        Path(output_path).write_bytes(zip_bytes)
        QMessageBox.information(self, "ICON", "Listo.")


def _activate_macos_app() -> None:
    try:
        from AppKit import NSApp, NSApplicationActivationPolicyRegular
    except ImportError:
        return
    NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    NSApp.activateIgnoringOtherApps_(True)


def _use_macos_fonts() -> None:
    import qfluentwidgets.common.font as font_mod

    original = font_mod.getFont

    def getFont(fontSize: int = 14, weight: QFont.Weight = QFont.Normal) -> QFont:
        font = QFont()
        font.setFamilies(["Helvetica Neue", "PingFang SC"])
        font.setPixelSize(fontSize)
        font.setWeight(weight)
        return font

    for module in list(sys.modules.values()):
        if getattr(module, "getFont", None) is original:
            module.getFont = getFont


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ICON")
    app.setApplicationDisplayName("ICON")
    app.setApplicationVersion(__version__)
    setTheme(Theme.DARK)
    setThemeColor(QColor(ACCENT))
    if APP_ICON_PNG.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PNG)))
    if sys.platform == "darwin":
        _use_macos_fonts()
        _activate_macos_app()
    window = IconWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
