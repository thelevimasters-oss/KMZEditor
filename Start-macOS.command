#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
export QT_OPENGL=software
export QTWEBENGINE_CHROMIUM_FLAGS="--disable-gpu --disable-gpu-compositing"
export QTWEBENGINE_DISABLE_SANDBOX=1
export KMZ_NO_WEBENGINE=1
if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display alert "Python 3 is required. Please install from python.org, then run this again."' || true
  exit 1
fi
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip wheel
pip install --prefer-binary -r requirements.txt
python -m kmz_studio
