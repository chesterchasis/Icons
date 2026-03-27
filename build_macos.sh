#!/bin/bash
set -e

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python="$root/.venv/bin/python"
icon_png="$root/assets/app_icon.png"
icon_icns="$root/assets/app_icon.icns"

if [ ! -f "$python" ]; then
  echo "Error: Python no encontrado en .venv"
  echo "Crea el entorno virtual: python3 -m venv .venv"
  exit 1
fi

echo "[1/4] Instalar dependencias"
cd "$root/engine"
"$python" -m pip install -r requirements.txt PyInstaller

if [ -f "$icon_png" ]; then
  echo "[2/4] Convertir assets/app_icon.png a ICNS"
  "$python" << 'EOF'
from PIL import Image
import os

icon_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "app_icon.png")
icon_icns = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "app_icon.icns")

# Abrir imagen PNG
img = Image.open(icon_png).convert("RGBA")

# Redimensionar a 1024x1024
img = img.resize((1024, 1024), Image.Resampling.LANCZOS)

# Guardar como ICNS
img.save(icon_icns, format="ICNS")
print(f"Icono convertido a: {icon_icns}")
EOF
else
  echo "[2/4] Sin icono personalizado en assets/app_icon.png"
fi

echo "[3/4] Compilar ICON.app"
if [ -f "$icon_icns" ]; then
  "$python" -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --onefile \
    --name ICON \
    --exclude-module PySide6 \
    --exclude-module PySide2 \
    --exclude-module PyQt6 \
    --icon "$icon_icns" \
    --osx-bundle-identifier "com.icongen.app" \
    desktop_app.py
else
  "$python" -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --onefile \
    --name ICON \
    --exclude-module PySide6 \
    --exclude-module PySide2 \
    --exclude-module PyQt6 \
    --osx-bundle-identifier "com.icongen.app" \
    desktop_app.py
fi

echo "[4/4] ¡Listo!"
echo "Aplicación generada en: engine/dist/ICON.app"
echo "Para ejecutar: open engine/dist/ICON.app"
