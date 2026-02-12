from __future__ import annotations

import numpy as np
import pytest

from api.src.services.streaming_audio_writer import (
    FORMAT_CONFIG,
    StreamingAudioWriter,
    encode_audio_complete,
    get_content_type,
)


class TestStreamingAudioWriter:
    def _make_pcm(self, duration: float = 0.5, sample_rate: int = 24000) -> np.ndarray:
        """Generate a sine wave as test PCM data."""
        t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
        return np.sin(2 * np.pi * 440 * t) * 0.5

    def test_pcm_format(self):
        writer = StreamingAudioWriter("pcm", 24000)
        pcm = self._make_pcm()
        result = writer.write_chunk(pcm)
        assert len(result) > 0
        # PCM int16: 2 bytes per sample
        assert len(result) == len(pcm) * 2

    def test_wav_format(self):
        pcm = self._make_pcm()
        result = encode_audio_complete(pcm, "wav", 24000)
        assert len(result) > 0
        # WAV header starts with RIFF
        assert result[:4] == b"RIFF"

    def test_mp3_format(self):
        pcm = self._make_pcm(duration=1.0)
        result = encode_audio_complete(pcm, "mp3", 24000)
        assert len(result) > 0

    def test_content_types(self):
        assert get_content_type("mp3") == "audio/mpeg"
        assert get_content_type("wav") == "audio/wav"
        assert get_content_type("pcm") == "audio/pcm"
        assert get_content_type("opus") == "audio/ogg"
        assert get_content_type("aac") == "audio/aac"
        assert get_content_type("flac") == "audio/flac"

    def test_streaming_mp3(self):
        writer = StreamingAudioWriter("mp3", 24000)
        pcm = self._make_pcm()
        chunk1 = writer.write_chunk(pcm)
        chunk2 = writer.write_chunk(pcm)
        final = writer.finalize()
        total = chunk1 + chunk2 + final
        assert len(total) > 0

    def test_format_config_complete(self):
        for fmt in ("mp3", "opus", "aac", "flac", "wav", "pcm"):
            assert fmt in FORMAT_CONFIG
            assert "content_type" in FORMAT_CONFIG[fmt]
