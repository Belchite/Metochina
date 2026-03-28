#!/usr/bin/env bash
# Metochina — Quick start script
# Usage: bash start.sh [arguments]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python
if ! command -v python3 &>/dev/null; then
    if command -v python &>/dev/null; then
        PYTHON=python
    else
        echo "Error: Python 3.11+ is required but not found."
        echo "Install it from https://www.python.org/downloads/"
        exit 1
    fi
else
    PYTHON=python3
fi

# Check version
PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using Python $PY_VERSION"

# Install dependencies
echo "Installing dependencies..."
$PYTHON -m pip install --quiet Pillow click

# Run
echo "Starting Metochina..."
$PYTHON -m metochina "$@"
