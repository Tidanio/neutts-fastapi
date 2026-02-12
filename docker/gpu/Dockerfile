FROM nvcr.io/nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3.10-venv python3-pip \
    espeak-ng libespeak-ng-dev \
    ffmpeg libsndfile1 \
    git curl \
    && rm -rf /var/lib/apt/lists/*

# espeak-ng environment
ENV PHONEMIZER_ESPEAK_LIBRARY=/usr/lib/x86_64-linux-gnu/libespeak-ng.so.1
ENV ESPEAK_DATA_PATH=/usr/lib/x86_64-linux-gnu/espeak-ng-data

# Install uv for fast dependency management
RUN pip install uv

# Create non-root user
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# Copy dependency file first for caching
COPY pyproject.toml .

# Install dependencies with GPU support
# Build llama-cpp-python with CUDA
ENV CMAKE_ARGS="-DGGML_CUDA=on"
RUN uv pip install --system ".[gpu]"

# Copy application code
COPY . .

# Fix permissions
RUN chown -R appuser:appuser /app
RUN mkdir -p /app/api/src/voices/custom && chown appuser:appuser /app/api/src/voices/custom

USER appuser

EXPOSE 8880

ENTRYPOINT ["bash", "entrypoint.sh"]
