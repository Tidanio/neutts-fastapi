from __future__ import annotations

import io
from typing import Literal

import av
import numpy as np

AudioFormat = Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]

# Mapping from our format names to PyAV codec/container names
FORMAT_CONFIG: dict[str, dict] = {
    "mp3": {"codec": "mp3", "container": "mp3", "content_type": "audio/mpeg"},
    "opus": {"codec": "libopus", "container": "ogg", "content_type": "audio/ogg"},
    "aac": {"codec": "aac", "container": "adts", "content_type": "audio/aac"},
    "flac": {"codec": "flac", "container": "flac", "content_type": "audio/flac"},
    "wav": {"codec": "pcm_s16le", "container": "wav", "content_type": "audio/wav"},
    "pcm": {"codec": None, "container": None, "content_type": "audio/pcm"},
}


def get_content_type(fmt: AudioFormat) -> str:
    return FORMAT_CONFIG[fmt]["content_type"]


class StreamingAudioWriter:
    """Encodes raw PCM audio (float32, mono) into various formats using PyAV."""

    def __init__(self, fmt: AudioFormat, sample_rate: int = 24000) -> None:
        self.format = fmt
        self.sample_rate = sample_rate
        self._buffer = io.BytesIO()

        if fmt == "pcm":
            # No encoding needed for raw PCM
            self._container = None
            self._stream = None
        else:
            config = FORMAT_CONFIG[fmt]
            self._container = av.open(self._buffer, mode="w", format=config["container"])
            self._stream = self._container.add_stream(config["codec"], rate=sample_rate)
            self._stream.layout = "mono"
            if fmt == "opus":
                self._stream.rate = 48000  # Opus requires 48kHz

    def write_chunk(self, pcm_data: np.ndarray) -> bytes:
        """Encode a chunk of float32 PCM audio and return the encoded bytes."""
        if self.format == "pcm":
            # Convert float32 to int16 PCM
            pcm_int16 = (pcm_data * 32767).astype(np.int16)
            return pcm_int16.tobytes()

        # Convert float32 [-1.0, 1.0] to int16
        pcm_int16 = (np.clip(pcm_data, -1.0, 1.0) * 32767).astype(np.int16)

        frame = av.AudioFrame.from_ndarray(
            pcm_int16.reshape(1, -1),
            format="s16",
            layout="mono",
        )
        frame.sample_rate = self.sample_rate
        if self.format == "opus":
            frame.sample_rate = 48000

        start_pos = self._buffer.tell()
        for packet in self._stream.encode(frame):
            self._container.mux(packet)

        # Read newly written bytes
        self._buffer.seek(start_pos)
        data = self._buffer.read()
        return data

    def finalize(self) -> bytes:
        """Flush remaining encoded data and close the container."""
        if self.format == "pcm" or self._container is None:
            return b""

        start_pos = self._buffer.tell()

        # Flush encoder
        for packet in self._stream.encode(None):
            self._container.mux(packet)

        self._container.close()

        self._buffer.seek(start_pos)
        data = self._buffer.read()
        return data

    def close(self) -> None:
        if self._container is not None:
            try:
                self._container.close()
            except Exception:
                pass
        self._buffer.close()


def encode_audio_complete(
    pcm_data: np.ndarray,
    fmt: AudioFormat,
    sample_rate: int = 24000,
) -> bytes:
    """Encode a complete PCM float32 array to the specified audio format."""
    if fmt == "pcm":
        return (pcm_data * 32767).astype(np.int16).tobytes()

    buf = io.BytesIO()
    config = FORMAT_CONFIG[fmt]
    container = av.open(buf, mode="w", format=config["container"])
    stream = container.add_stream(config["codec"], rate=sample_rate)
    stream.layout = "mono"

    actual_rate = 48000 if fmt == "opus" else sample_rate
    if fmt == "opus":
        stream.rate = 48000

    pcm_int16 = (np.clip(pcm_data, -1.0, 1.0) * 32767).astype(np.int16)
    frame = av.AudioFrame.from_ndarray(
        pcm_int16.reshape(1, -1),
        format="s16",
        layout="mono",
    )
    frame.sample_rate = actual_rate

    for packet in stream.encode(frame):
        container.mux(packet)
    for packet in stream.encode(None):
        container.mux(packet)
    container.close()

    buf.seek(0)
    return buf.read()
