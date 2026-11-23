@echo off
REM Doble clic para arrancar el bot en Windows.
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo No se encontro el entorno .venv. Sigue el Paso 4 de GUIA_WINDOWS.md
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m binance_bot.bot
pause
