#!/usr/bin/env bash
#
# Idempotent bootstrap for the Python games collection.
#   - Installs the system libraries pygame/pymunk need at runtime, plus a
#     virtual display (Xvfb) and capture tools so the GUI games can run and be
#     screenshotted in a headless cloud environment.
#   - Creates a shared .venv and installs every game's declared dependencies.
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  python3.12-venv python3-dev build-essential pkg-config \
  xvfb x11-utils xdotool ffmpeg \
  libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 \
  libfreetype6 libjpeg-turbo8 libpng16-16 libportmidi0

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip wheel

# Install each game's declared dependencies. Sorted for deterministic ordering;
# pip resolves the (compatible) pygame pins across games to a single version.
while IFS= read -r req; do
  echo ">>> Installing dependencies from ${req}"
  pip install -r "$req"
done < <(find . -name requirements.txt -not -path './.venv/*' | sort)

echo
echo "Environment ready. Run a GUI game headlessly with, e.g.:"
echo "  source .venv/bin/activate"
echo "  DISPLAY=:99 SDL_AUDIODRIVER=dummy python BlumgiMerge/main.py"
