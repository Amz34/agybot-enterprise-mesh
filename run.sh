#!/usr/bin/env bash
# Daemon script to run AgyBot Sovereign Mesh
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

export AGYBOT_PORT=8800
export AGYBOT_HOST=0.0.0.0

echo "Starting AgyBot Sovereign Mesh Gateway on http://0.0.0.0:8800 ..."
exec python3 server.py
