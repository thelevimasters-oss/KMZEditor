@echo on
setlocal EnableExtensions EnableDelayedExpansion
title KMZ Studio (Portable, No Embedded Map)

set QT_OPENGL=software
set QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu --disable-gpu-compositing
set QTWEBENGINE_DISABLE_SANDBOX=1
set KMZ_NO_WEBENGINE=1

set "PYEXE="
where python >nul 2>nul && (set "PYEXE=python")
if not defined PYEXE (
  where py >nul 2>nul && (for /f "usebackq delims=" %%I in (`py -3 -c "import sys;print(sys.executable)"`) do set "PYEXE=%%~I")
)
if not defined PYEXE (
  for /f "usebackq delims=" %%D in (`powershell -NoP -C "$p="$env:LocalAppData+'\Programs\Python'; if(Test-Path $p){Get-ChildItem $p -Filter Python3* -Dir | Sort-Object Name -Descending | Select-Object -First 1 | %%{ Join-Path $_.FullName 'python.exe' }}"`) do (
    if exist "%%D" set "PYEXE=%%D"
  )
)
if not defined PYEXE (
  echo Could not find Python. Please install Python (64-bit) and re-run.
  pause
  exit /b 1
)
echo Using Python: %PYEXE%
if not exist .venv (
  "%PYEXE%" -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip wheel
pip install --prefer-binary -r requirements.txt
python -m kmz_studio
pause
