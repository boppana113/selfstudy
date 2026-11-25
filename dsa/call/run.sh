#!/bin/bash
# Start a live voice mock. /dsa writes the brief first (`/dsa call`).
# Flags pass through to server.py: --model claude-sonnet-5-5  --effort low  --port 8765
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "first run: creating the environment…"
  uv venv -q --python 3.12 .venv
  uv pip install -q --python .venv/bin/python -r requirements.txt
fi
exec .venv/bin/python server.py "$@"
