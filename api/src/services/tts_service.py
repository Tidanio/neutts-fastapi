from __future__ import annotations

from typing import AsyncGenerator

import numpy as np
from loguru import logger

from api.src.core.config import settings
from api.src.core.model_config import BackendType, get_backbone_info
from api.src.inference.model_manager import ModelManager
from api.src.inference.text_chunker import chunk_text
from api.src.inference.voice_manager import VoiceManager
from api.src.services.streaming_audio_writer import (
    AudioFormat,
    StreamingAudioWriter,
    encode_audio_complete,
)
from api.src.structures.schemas import OpenAISpeechRequest


def _apply_speed(wav: np.ndarray, speed: float) -> np.ndarray:
    """Adjust audio playback speed via resampling."""
    if speed == 1.0:
        return wav
    # Resample: fewer samples = faster, more samples = slower
    new_length = int(len(wav) / speed)
    indices = np.linspace(0, len(wav) - 1, new_length)
    return np.interp(indices, np.arange(len(wav)), wav).astype(np.float32)


class TTSService:
    _instance: TTSService | None = None

    def __init__(self) -> None:
        self._model_manager = ModelManager.get_instance()
        self._voice_manager = VoiceManager.get_instance()

    @classmethod
    def get_instance(cls) -> TTSService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def generate_speech(self, request: OpenAISpeechRequest) -> bytes:
        """Generate complete audio from text."""
        model_id = request.model
        voice = request.voice
        fmt: AudioFormat = request.response_format

        # Ensure model is loaded
        if not self._model_manager.is_loaded(model_id):
            raise ValueError(f"Model '{model_id}' is not loaded")

        loaded = self._model_manager.loaded_models[model_id]

        # Get voice reference
        ref_codes = await self._voice_manager.get_or_encode_ref_codes(
            voice, loaded.codec_id, self._model_manager, model_id
        )
        ref_text = self._voice_manager.get_ref_text(voice)

        # For short text, single inference
        text = request.input.strip()
        info = get_backbone_info(model_id)

        if len(text) <= 500 or info is None:
            wav = await self._model_manager.infer(model_id, text, ref_codes, ref_text)
            wav = _apply_speed(wav, request.speed)
            return encode_audio_complete(wav, fmt, settings.sample_rate)

        # For long text, chunk and concatenate
        chunks = chunk_text(text)
        wav_parts: list[np.ndarray] = []

        for chunk in chunks:
            wav = await self._model_manager.infer(model_id, chunk, ref_codes, ref_text)
            wav_parts.append(wav)

        full_wav = np.concatenate(wav_parts)
        full_wav = _apply_speed(full_wav, request.speed)
        return encode_audio_complete(full_wav, fmt, settings.sample_rate)

    async def stream_speech(
        self, request: OpenAISpeechRequest
    ) -> AsyncGenerator[bytes, None]:
        """Stream audio chunks as they are generated."""
        model_id = request.model
        voice = request.voice
        fmt: AudioFormat = request.response_format

        if not self._model_manager.is_loaded(model_id):
            raise ValueError(f"Model '{model_id}' is not loaded")

        loaded = self._model_manager.loaded_models[model_id]
        info = get_backbone_info(model_id)

        ref_codes = await self._voice_manager.get_or_encode_ref_codes(
            voice, loaded.codec_id, self._model_manager, model_id
        )
        ref_text = self._voice_manager.get_ref_text(voice)

        text = request.input.strip()
        writer = StreamingAudioWriter(fmt, settings.sample_rate)

        speed = request.speed

        try:
            if info and info.supports_streaming:
                # Real streaming with GGUF models
                async for chunk in self._model_manager.infer_stream(
                    model_id, text, ref_codes, ref_text
                ):
                    chunk = _apply_speed(chunk, speed)
                    encoded = writer.write_chunk(chunk)
                    if encoded:
                        yield encoded
            else:
                # Pseudo-streaming: chunk text, infer per chunk
                chunks = chunk_text(text)
                for chunk in chunks:
                    wav = await self._model_manager.infer(
                        model_id, chunk, ref_codes, ref_text
                    )
                    wav = _apply_speed(wav, speed)
                    encoded = writer.write_chunk(wav)
                    if encoded:
                        yield encoded

            # Finalize
            final = writer.finalize()
            if final:
                yield final
        finally:
            writer.close()
