#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontró python3. Instálalo desde https://www.python.org/downloads/"
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

echo "Lanzando el juego..."
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"
python -m equestrian.main
