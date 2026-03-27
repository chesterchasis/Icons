from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QImage, QPixmap, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    DoubleSpinBox,
    PrimaryPushButton,
    PushButton,
    Slider,
    StrongBodyLabel,
    SubtitleLabel,
    TitleLabel,
    Theme,
    setTheme,
    setThemeColor,
)

from icon_processor import export_icons_zip, open_image_rgba, render_preview

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"
APP_ICON_PNG = ASSETS_DIR / "app_icon.png"
APP_ICON_ICO = ASSETS_DIR / "app_icon.ico"


class IconWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ICON")
        self.resize(1240, 820)
        self.image_path: Path | None = None
        self.source_image: Image.Image | None = None
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.update_preview)

        self.platform_combo = ComboBox()
        self.platform_combo.addItems(["all", "windows", "macos", "ios", "android"])

        self.frame_combo = ComboBox()
        self.frame_combo.addItems(["rounded", "circle", "square"])

        self.zoom_slider = self._create_slider(50, 300, 100)
        self.zoom_spin = self._create_spin(0.50, 3.00, 0.01, 1.00)
        self.move_x_slider = self._create_slider(-100, 100, 0)
        self.move_x_spin = self._create_spin(-1.00, 1.00, 0.01, 0.00)
        self.move_y_slider = self._create_slider(-100, 100, 0)
        self.move_y_spin = self._create_spin(-1.00, 1.00, 0.01, 0.00)

        self.status_label = StrongBodyLabel("Selecciona una imagen para empezar.")
        self.hint_label = BodyLabel("Flujo: 1) Abrir imagen  2) Ajustar  3) Exportar ZIP")
        self.preview_label = BodyLabel("Sin vista previa")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(520, 520)

        self._build_ui()
        self._wire_events()
        self._apply_theme()
        self._apply_window_icon()

    def _create_slider(self, minimum: int, maximum: int, value: int) -> Slider:
        slider = Slider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        return slider

    def _create_spin(self, minimum: float, maximum: float, step: float, value: float) -> DoubleSpinBox:
        spin = DoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setDecimals(2)
        spin.setAccelerated(True)
        spin.setValue(value)
        return spin

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QGridLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(18)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        controls_layout.setSpacing(14)

        title = TitleLabel("ICON")
        subtitle = SubtitleLabel("Generador de iconos multiplataforma")
        controls_layout.addWidget(title)
        controls_layout.addWidget(subtitle)
        controls_layout.addWidget(self.hint_label)

        controls_layout.addLayout(self._row("1) Plataforma", self.platform_combo))
        controls_layout.addLayout(self._row("2) Frame", self.frame_combo))
        controls_layout.addLayout(self._slider_row("3) Zoom", self.zoom_slider, self.zoom_spin, self.nudge_zoom_minus, self.nudge_zoom_plus))
        controls_layout.addLayout(self._slider_row("4) Mover X", self.move_x_slider, self.move_x_spin, self.nudge_move_x_minus, self.nudge_move_x_plus))
        controls_layout.addLayout(self._slider_row("5) Mover Y", self.move_y_slider, self.move_y_spin, self.nudge_move_y_minus, self.nudge_move_y_plus))

        buttons = QHBoxLayout()
        self.open_button = PrimaryPushButton("Abrir imagen")
        self.reset_button = PushButton("Reset ajuste")
        self.export_button = PrimaryPushButton("Exportar ZIP")
        buttons.addWidget(self.open_button)
        buttons.addWidget(self.reset_button)
        buttons.addWidget(self.export_button)
        controls_layout.addLayout(buttons)
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch(1)

        preview_box = QWidget()
        preview_layout = QVBoxLayout(preview_box)
        preview_title = SubtitleLabel("Vista previa en vivo")
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.preview_label, 0, Qt.AlignCenter)
        preview_layout.addStretch(1)

        layout.addWidget(controls, 0, 0)
        layout.addWidget(preview_box, 0, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

    def _row(self, label_text: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        label = StrongBodyLabel(label_text)
        label.setMinimumWidth(92)
        row.addWidget(label)
        row.addWidget(widget, 1)
        return row

    def _slider_row(self, label_text: str, slider: Slider, spin: DoubleSpinBox, minus_cb, plus_cb) -> QVBoxLayout:
        wrapper = QVBoxLayout()
        top = QHBoxLayout()
        label = StrongBodyLabel(label_text)
        label.setMinimumWidth(92)
        minus_button = PushButton("-")
        minus_button.clicked.connect(minus_cb)
        plus_button = PushButton("+")
        plus_button.clicked.connect(plus_cb)
        minus_button.setFixedWidth(34)
        plus_button.setFixedWidth(34)
        top.addWidget(label)
        top.addWidget(spin)
        top.addWidget(minus_button)
        top.addWidget(plus_button)
        wrapper.addLayout(top)
        wrapper.addWidget(slider)
        return wrapper

    def _wire_events(self) -> None:
        self.open_button.clicked.connect(self.select_image)
        self.reset_button.clicked.connect(self.reset_adjustments)
        self.export_button.clicked.connect(self.export_zip)
        self.platform_combo.currentTextChanged.connect(self.schedule_preview)
        self.frame_combo.currentTextChanged.connect(self.schedule_preview)

        self.zoom_slider.valueChanged.connect(lambda value: self._sync_slider_to_spin(self.zoom_spin, value / 100.0))
        self.move_x_slider.valueChanged.connect(lambda value: self._sync_slider_to_spin(self.move_x_spin, value / 100.0))
        self.move_y_slider.valueChanged.connect(lambda value: self._sync_slider_to_spin(self.move_y_spin, value / 100.0))

        self.zoom_spin.valueChanged.connect(lambda value: self._sync_spin_to_slider(self.zoom_slider, value * 100))
        self.move_x_spin.valueChanged.connect(lambda value: self._sync_spin_to_slider(self.move_x_slider, value * 100))
        self.move_y_spin.valueChanged.connect(lambda value: self._sync_spin_to_slider(self.move_y_slider, value * 100))

    def _sync_slider_to_spin(self, spin: DoubleSpinBox, value: float) -> None:
        if abs(spin.value() - value) > 0.001:
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        self.schedule_preview()

    def _sync_spin_to_slider(self, slider: Slider, value: float) -> None:
        int_value = int(round(value))
        if slider.value() != int_value:
            slider.blockSignals(True)
            slider.setValue(int_value)
            slider.blockSignals(False)
        self.schedule_preview()

    def _apply_window_icon(self) -> None:
        if APP_ICON_ICO.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_ICO)))
        elif APP_ICON_PNG.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))

    def _apply_theme(self) -> None:
        setTheme(Theme.LIGHT)
        setThemeColor(QColor("#39B6E8"))
        self.setStyleSheet(
            """
            QMainWindow {
                background: #eef3fb;
            }
            QWidget {
                color: #14233b;
                font-size: 14px;
            }
            """
        )
        self.preview_label.setStyleSheet(
            "border: 1px solid #4f7db1; border-radius: 20px; background: #1e4676; color: #f2f8ff; padding: 12px;"
        )
        self.hint_label.setStyleSheet("color: #35506f;")
        self.status_label.setStyleSheet(
            "color: #0f2747; background: #dcecff; border: 1px solid #8cb3df; border-radius: 10px; padding: 8px;"
        )

    def current_frame(self) -> str:
        return self.frame_combo.currentText()

    def current_platform(self) -> str:
        return self.platform_combo.currentText()

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
        self.status_label.setText("Ajustes reiniciados.")

    def select_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecciona una imagen", str(Path.home()), "Imagenes (*.png *.jpg *.jpeg *.webp)")
        if not file_path:
            return

        self.image_path = Path(file_path)
        self.source_image = open_image_rgba(self.image_path)
        self.status_label.setText(f"Imagen cargada: {self.image_path.name}")
        self.schedule_preview()

    def schedule_preview(self) -> None:
        if self.source_image is None:
            return
        self.status_label.setText("Actualizando vista previa...")
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
        scaled = pixmap.scaled(430, 430, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
        self.status_label.setText("Vista previa actualizada.")

    def export_zip(self) -> None:
        if self.source_image is None:
            QMessageBox.warning(self, "Falta imagen", "Primero abre una imagen.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Guardar ZIP", str(Path.home() / "ICON-export.zip"), "ZIP (*.zip)")
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
        self.status_label.setText(f"Exportado: {Path(output_path).name}")
        QMessageBox.information(self, "Exportado", "ZIP generado correctamente.")


def main() -> int:
    app = QApplication(sys.argv)
    window = IconWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
