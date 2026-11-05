#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python3 scripts/generate_desktop.py
python3 scripts/verify_text.py
printf '%s\n' 'Preview: http://127.0.0.1:8765/preview.html'
exec python3 -m http.server 8765 --bind 127.0.0.1
