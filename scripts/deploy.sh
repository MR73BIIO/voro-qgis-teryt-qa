#!/usr/bin/env bash
# Copies the plugin from the repo (WSL) into the QGIS profile on Windows.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO/voro_teryt_qa"
APPDATA_WIN="$(cmd.exe /c 'echo %APPDATA%' 2>/dev/null | tr -d '\r')"
DST="$(wslpath "$APPDATA_WIN")/QGIS/QGIS3/profiles/default/python/plugins/voro_teryt_qa"
[ -f "$SRC/metadata.txt" ] || { echo "No plugin in $SRC"; exit 1; }
rm -rf "$DST"
mkdir -p "$DST"
cp -r "$SRC"/. "$DST"/
find "$DST" -name '__pycache__' -prune -exec rm -rf {} +
echo "Copied to: $DST"
ls -l "$DST"
