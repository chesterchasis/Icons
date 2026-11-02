#!/bin/zsh
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -x "$root/.venv/bin/python" ]]; then
  echo "Creando entorno virtual..."
  python3 -m venv "$root/.venv"
  "$root/.venv/bin/python" -m pip install --upgrade pip
  "$root/.venv/bin/python" -m pip install -r "$root/engine/requirements.txt"
fi

exec "$root/.venv/bin/python" "$root/engine/main.py"
