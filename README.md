# ICON

Generador de iconos multiplataforma como aplicación de escritorio nativa.

Disponible para **Windows** y **macOS**.

## Arquitectura

La app está construida como aplicación de escritorio nativa con PyQt5 (sin navegador web).

- **Windows**: `.exe` ejecutable nativo
- **macOS**: `.app` empaquetado para macOS

## Flujo de uso (MVP)

1. Seleccionas la plataforma destino del icono
2. Subes una imagen
3. Eliges frame: `rounded`, `circle` o `square`
4. Ajustas zoom y posición manualmente
5. Ves vista previa en vivo
6. Exportas un ZIP con los iconos generados

## Estructura del proyecto

```
├── engine/
│   ├── desktop_app.py         # Interfaz PyQt5
│   ├── icon_processor.py       # Procesamiento y export
│   ├── main.py                 # Punto de entrada
│   ├── requirements.txt         # Dependencias
│   └── requirements-dev.txt     # Dependencias dev (tests)
├── build_windows.ps1           # Build para Windows
├── build_macos.sh              # Build para macOS
└── assets/
    └── app_icon.png            # Icono fuente (1024x1024)
```

## Requisitos previos

### Windows
- Python 3.8 o superior
- PowerShell 5.0+
- pip (gestor de paquetes Python)

### macOS
- Python 3.8 o superior
- Terminal (bash/zsh)
- pip (gestor de paquetes Python)

---

# 🪟 INSTALACIÓN Y COMPILACIÓN - WINDOWS

## Paso 1: Descargar el proyecto

```powershell
git clone https://github.com/tu-usuario/Icons.git
cd Icons
```

O si descargaste el ZIP:
```powershell
cd tu-carpeta/Icons
```

## Paso 2: Crear entorno virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si te pide permiso, ejecuta:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Paso 3: Instalar dependencias

```powershell
pip install -r engine/requirements.txt
```

## Paso 4: Ejecutar en desarrollo (opcional)

```powershell
.\.venv\Scripts\python.exe .\engine\main.py
```

## Paso 5: Compilar aplicación (.exe)

Desde la raíz del proyecto:

```powershell
.\build_windows.ps1
```

**Resultado**: `engine/dist/ICON.exe`

### Notas instalación icono personalizado

1. Antes del build, coloca tu icono aquí: `assets/app_icon.png`
2. Formato recomendado: PNG cuadrado de 1024x1024 píxeles
3. El script genera automáticamente `assets/app_icon.ico` para Windows
4. Si no colocas icono, se usa uno por defecto

### Troubleshooting Windows

**Error: "No se puede ejecutar Scripts/Activate.ps1"**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Error: "python: command not found"**
- Descarga Python de https://www.python.org/downloads/
- En el instalador, marca: ✓ "Add Python to PATH"

---

# 🍎 INSTALACIÓN Y COMPILACIÓN - macOS

## Paso 1: Descargar el proyecto

```bash
git clone https://github.com/tu-usuario/Icons.git
cd Icons
```

O si descargaste el ZIP:
```bash
cd tu-carpeta/Icons
```

## Paso 2: Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Paso 3: Instalar dependencias

```bash
pip install -r engine/requirements.txt
```

## Paso 4: Ejecutar en desarrollo (opcional)

```bash
.venv/bin/python engine/main.py
```

## Paso 5: Compilar aplicación (.app)

Desde la raíz del proyecto:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

**Resultado**: `engine/dist/ICON.app`

### Ejecutar la app compilada

```bash
open engine/dist/ICON.app
```

O doble-clic en `engine/dist/ICON.app` desde Finder.

### Notas instalación icono personalizado

1. Coloca tu icono aquí: `assets/app_icon.png`
2. Formato recomendado: PNG cuadrado de 1024x1024 píxeles
3. El script genera automáticamente `assets/app_icon.icns` para macOS
4. Si no colocas icono, se usa uno por defecto

### Troubleshooting macOS

**Error: "python3: command not found"**
- Instala Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- Luego: `brew install python3`

**Error: "Permission denied" al ejecutar build_macos.sh**
```bash
chmod +x build_macos.sh
./build_macos.sh
```

**Advertencia: "Cannot open ICON.app"**
- Abre Finder, ve a `engine/dist/`
- Haz clic derecho en `ICON.app` → "Abrir"
- Confirma en la ventana de seguridad

---

# 🧪 Tests (el desarrollo)

Desde la carpeta `engine`:

### Windows
```powershell
.\..\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\..\venv\Scripts\python.exe -m pytest -v
```

### macOS
```bash
../.venv/bin/python -m pip install -r requirements-dev.txt
../.venv/bin/python -m pytest -v
```

---

# 📝 Licencia

MIT

---

## Soporte

Si encuentras problemas:
1. Verifica que Python 3.8+ está instalado: `python --version` (Windows) o `python3 --version` (macOS)
2. Asegúrate que el entorno virtual está activado (ves `(.venv)` al inicio de la terminal)
3. Revisa la carpeta `engine/dist/` después del build
