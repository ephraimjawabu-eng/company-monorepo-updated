#!/usr/bin/env bash
# Create a portable Python venv bundle for offline distribution (Linux/macOS)
set -euo pipefail
ROOT=$(dirname "$0")/..
ROOT=$(cd "$ROOT" && pwd)
DIST_DIR="$ROOT/dist/py-bundle"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
python -m venv "$DIST_DIR/venv"
# activate and install deps
source "$DIST_DIR/venv/bin/activate"
pip install --upgrade pip
if [ -f "$ROOT/services/api/requirements.txt" ]; then
  pip install -r "$ROOT/services/api/requirements.txt"
fi
# copy source
mkdir -p "$DIST_DIR/app"
rsync -a --exclude='*.pyc' --exclude='__pycache__' "$ROOT/" "$DIST_DIR/app/"
# create a launcher
cat > "$DIST_DIR/run.sh" <<'SH'
#!/usr/bin/env bash
DIR=$(cd "$(dirname "$0")" && pwd)
source "$DIR/venv/bin/activate"
python "$DIR/app/services/api/main.py"
SH
chmod +x "$DIST_DIR/run.sh"
# archive
cd "$ROOT/dist"
ZIP_NAME="py-bundle-$(date +%Y%m%d%H%M%S).zip"
zip -r "$ZIP_NAME" py-bundle
echo "Created $PWD/$ZIP_NAME"
