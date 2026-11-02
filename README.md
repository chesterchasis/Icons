# ICON

Aplicación de escritorio para generar un pack de iconos a partir de una imagen. Una sola fuente, vista previa en vivo y un ZIP con los tamaños de Windows, macOS, iOS y Android.

<p align="center">
  <img src="assets/app_icon.png" width="88" alt="Icono de ICON">
</p>

## Uso

1. Abre o arrastra una imagen (PNG, JPG, WEBP).
2. Elige plataforma y forma.
3. Ajusta zoom y posición.
4. Exporta el ZIP.

| Destino | Contenido |
| --- | --- |
| Windows | `icon.ico` y PNG de 16 a 1024 px |
| macOS | PNG de 128, 256, 512 y 1024 px |
| iOS | App icons de 60 a 1024 px |
| Android | `ic_launcher` en mdpi–xxxhdpi |
| Todas | Las cuatro carpetas en un ZIP |

## Ejecutar

Requisito: Python 3.9+.

**macOS**

```bash
./start_macos.sh
```

**Windows**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r engine/requirements.txt
.\.venv\Scripts\python.exe .\engine\main.py
```

## Compilar

| Sistema | Comando | Salida |
| --- | --- | --- |
| macOS | `./build_macos.sh` | `engine/dist/ICON.app` |
| Windows | `.\build_windows.ps1` | `engine/dist/ICON.exe` |

```bash
open engine/dist/ICON.app
```

El icono de la aplicación es `assets/app_icon.png` (1024×1024). El build genera `.icns` y `.ico`.

## Proyecto

```
engine/desktop_app.py     interfaz
engine/icon_processor.py  recorte, tamaños y ZIP
engine/main.py            entrada
assets/app_icon.png       icono de producto
start_macos.sh            arranque en macOS
build_macos.sh            paquete .app
build_windows.ps1         paquete .exe
```

## Tests

```bash
cd engine
../.venv/bin/python -m pip install -r requirements-dev.txt
../.venv/bin/python -m pytest -v
```

## Licencia

MIT
