#!/usr/bin/env bash
# Builds the plugin ZIP for plugins.qgis.org from what is COMMITTED (git archive),
# so the ZIP matches the repository and has no __pycache__, .git or other leftovers.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
if [ -n "$(git status --porcelain voro_teryt_qa)" ]; then
  echo "Uncommitted changes in voro_teryt_qa - commit them first:"
  git status --short voro_teryt_qa
  exit 1
fi
VERSION="$(sed -n 's/^version=//p' voro_teryt_qa/metadata.txt | tr -d '\r')"
mkdir -p dist
OUT="dist/voro_teryt_qa-$VERSION.zip"
rm -f "$OUT"
git archive --format=zip --output="$OUT" HEAD voro_teryt_qa
python3 - "$OUT" <<'PY'
import sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
names = z.namelist()
size = sum(i.file_size for i in z.infolist())
for n in names:
    print(" ", n)
need = ["voro_teryt_qa/metadata.txt", "voro_teryt_qa/__init__.py", "voro_teryt_qa/LICENSE", "voro_teryt_qa/icon.png"]
missing = [n for n in need if n not in names]
junk = [n for n in names if "__pycache__" in n or n.endswith(".pyc") or "/.git" in n]
print(f"files: {len(names)} | unpacked size: {size} bytes")
if missing or junk:
    sys.exit(f"PROBLEM - missing: {missing}, junk: {junk}")
print("ZIP OK")
PY
echo "Built: $OUT"
