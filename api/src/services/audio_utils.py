from __future__ import annotations

import io

import numpy as np
import soundfile as sf


def validate_wav(data: bytes) -> dict:
    """Validate a WAV file and return its properties."""
    buf = io.BytesIO(data)
    try:
        info = sf.info(buf)
    except Exception as e:
        raise ValueError(f"Invalid WAV file: {e}") from e

    return {
        "sample_rate": info.samplerate,
        "channels": info.channels,
        "duration": info.duration,
        "frames": info.frames,
        "format": info.format,
    }


def validate_reference_audio(data: bytes) -> dict:
    """Validate reference audio for voice cloning.

    Requirements:
    - Mono channel
    - 16-44 kHz sample rate
    - 3-15 seconds duration
    """
    props = validate_wav(data)

    if props["channels"] != 1:
        raise ValueError(
            f"Reference audio must be mono (1 channel), got {props['channels']} channels"
        )

    if not (8000 <= props["sample_rate"] <= 48000):
        raise ValueError(
            f"Reference audio sample rate must be 8-48 kHz, got {props['sample_rate']} Hz"
        )

    if props["duration"] < 1.0:
        raise ValueError(
            f"Reference audio too short ({props['duration']:.1f}s), minimum 1 second"
        )

    if props["duration"] > 30.0:
        raise ValueError(
            f"Reference audio too long ({props['duration']:.1f}s), maximum 30 seconds"
        )

    return props


def pcm_to_wav_bytes(pcm_data: np.ndarray, sample_rate: int = 24000) -> bytes:
    """Convert float32 PCM numpy array to WAV bytes."""
    buf = io.BytesIO()
    sf.write(buf, pcm_data, sample_rate, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return buf.read()
