@echo on
setlocal EnableExtensions EnableDelayedExpansion
title KMZ Studio (Force Python 3.11, No Embedded Map)

set QT_OPENGL=software
set QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu --disable-gpu-compositing
set QTWEBENGINE_DISABLE_SANDBOX=1
set KMZ_NO_WEBENGINE=1

set "PY311="
where py >nul 2>nul && (for /f "usebackq delims=" %%I in (`py -3.11 -c "import sys;print(sys.executable)" 2^>nul`) do set "PY311=%%~I")
if not defined PY311 (
  echo Python 3.11 not found. Attempting install via winget...
  winget --version >nul 2>nul
  if %ERRORLEVEL% NEQ 0 (
    echo winget not available. Please install Python 3.11 from python.org and re-run.
    pause
    exit /b 1
  )
  winget install -e --id Python.Python.3.11 --source winget --accept-source-agreements --accept-package-agreements
  for /f "usebackq delims=" %%I in (`py -3.11 -c "import sys;print(sys.executable)" 2^>nul`) do set "PY311=%%~I"
)
if not defined PY311 (
  echo Still could not locate Python 3.11. Aborting.
  pause
  exit /b 1
)
echo Using Python 3.11: %PY311%
if not exist .venv (
  "%PY311%" -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip wheel
pip install --prefer-binary -r requirements.txt
python -m kmz_studio
pause
