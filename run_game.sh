#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 no encontrado. Instalalo desde https://www.python.org/downloads/"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Creando entorno virtual..."
  python3 -m venv .venv
fi

source ".venv/bin/activate"

echo "Instalando dependencias..."
python -m pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null

export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"
echo "Lanzando el juego..."
python -m equestrian.main
