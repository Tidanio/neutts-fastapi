#!/usr/bin/env bash
# macOS double-click launcher
# This file can be opened in Finder to start NeuTTS-FastAPI

# Navigate to the script's directory (needed for Finder double-click)
cd "$(dirname "$0")" || exit 1

# Run the main start script
exec ./start.sh
