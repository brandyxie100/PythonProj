#!/bin/sh
set -e

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Error: Python 3 is not installed. Install Python 3 or run 'xcode-select --install' on macOS." >&2
  exit 1
fi

$PY -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Environment created. Activate it with 'source .venv/bin/activate' and run 'python main.py'."