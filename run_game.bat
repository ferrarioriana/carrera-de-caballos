@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

where python >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python en el PATH. Instalalo desde https://www.python.org/downloads/
  exit /b 1
)

if not exist ".venv" (
  echo Creando entorno virtual...
  python -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo Instalando dependencias...
python -m pip install --upgrade pip >nul
if errorlevel 1 (
  echo Error actualizando pip.
  exit /b 1
)
pip install -r requirements.txt >nul
if errorlevel 1 (
  echo Error instalando dependencias.
  exit /b 1
)

set "PYTHONPATH=%SCRIPT_DIR%src;%PYTHONPATH%"
echo Lanzando el juego...
python -m equestrian.main
if errorlevel 1 (
  echo El juego terminó con errores.
  exit /b 1
)

endlocal
exit /b 0
