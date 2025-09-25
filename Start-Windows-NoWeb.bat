@echo on
setlocal
title KMZ Studio (No Embedded Map)

set QT_OPENGL=software
set QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu --disable-gpu-compositing
set QTWEBENGINE_DISABLE_SANDBOX=1
set KMZ_NO_WEBENGINE=1

where python >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required. If not on PATH, run Start-Windows-Portable-NoWeb.bat or Start-Windows-Force311-NoWeb.bat
  pause
  exit /b 1
)
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip wheel
pip install --prefer-binary -r requirements.txt
python -m kmz_studio
pause
