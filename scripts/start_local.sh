#!/usr/bin/env bash
# Start local backend and optionally Electron UI (UNIX)
START_ELECTRON=${1:-}
export PYTHONPATH="$(dirname "$0")/.."
python services/api/main.py &
sleep 2
if [ "$START_ELECTRON" = "--electron" ]; then
  pushd apps/native
  if [ ! -d node_modules ]; then
    echo "Installing electron..."
    npm install
  fi
  npm run start &
  popd
fi
echo "Local services started. Backend: http://127.0.0.1:8000"
