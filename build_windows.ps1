$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$iconPng = Join-Path $root "assets\app_icon.png"
$iconIco = Join-Path $root "assets\app_icon.ico"

if (-not (Test-Path $python)) {
  throw "No se encontro Python en .venv. Crea el entorno virtual en la raiz del proyecto."
}

Write-Host "[1/4] Instalar dependencias de build"
Set-Location (Join-Path $root "engine")
& $python -m pip install -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Fallo instalando dependencias" }

if (Test-Path $iconPng) {
  Write-Host "[2/4] Convertir assets\\app_icon.png a ICO"
  & $python -c "from PIL import Image; img=Image.open(r'$iconPng').convert('RGBA'); img.save(r'$iconIco', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
  if ($LASTEXITCODE -ne 0) { throw "Fallo convirtiendo icono PNG a ICO" }
} else {
  Write-Host "[2/4] Sin icono personalizado, se compila sin icono de EXE"
}

Write-Host "[3/4] Compilar ICON.exe"
$pyi = @(
  "-m", "PyInstaller",
  "--noconfirm", "--clean", "--windowed", "--onefile",
  "--name", "ICON",
  "--exclude-module", "PySide6",
  "--exclude-module", "PySide2",
  "--exclude-module", "PyQt6",
  "--add-data", "$root\VERSION;.",
  "--add-data", "$root\assets\app_icon.png;assets"
)
if (Test-Path $iconIco) { $pyi += @("--icon", $iconIco) }
& $python @pyi desktop_app.py
if ($LASTEXITCODE -ne 0) { throw "Fallo compilando ICON.exe" }

Write-Host "[4/4] Listo"
Write-Host "Ejecutable generado en: engine\dist\ICON.exe"
