#!/bin/bash
set -e

# Ensure espeak-ng data is accessible
export PHONEMIZER_ESPEAK_LIBRARY=${PHONEMIZER_ESPEAK_LIBRARY:-/usr/lib/x86_64-linux-gnu/libespeak-ng.so.1}
export ESPEAK_DATA_PATH=${ESPEAK_DATA_PATH:-/usr/lib/x86_64-linux-gnu/espeak-ng-data}

# Optional: pre-download models
if [ "${NEUTTS_PREDOWNLOAD_MODELS:-false}" = "true" ]; then
    echo "Pre-downloading models..."
    python -m docker.scripts.download_models
fi

echo "Starting NeuTTS-FastAPI server..."
exec uvicorn api.src.main:app \
    --host "${NEUTTS_HOST:-0.0.0.0}" \
    --port "${NEUTTS_PORT:-8880}" \
    --workers 1 \
    --log-level "${NEUTTS_LOG_LEVEL:-info}"
