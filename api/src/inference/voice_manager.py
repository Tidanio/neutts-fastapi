from __future__ import annotations

import shutil
from pathlib import Path

import torch
from loguru import logger

from api.src.core.config import settings
from api.src.core.model_config import BUILTIN_VOICES
from api.src.core.paths import (
    BUILTIN_VOICES_DIR,
    CUSTOM_VOICES_DIR,
    ensure_voice_dirs,
    get_voice_codes,
    get_voice_text,
    get_voice_wav,
    is_custom_voice,
    voice_codes_path,
)


class VoiceManager:
    _instance: VoiceManager | None = None

    def __init__(self) -> None:
        self._voices: dict[str, dict] = {}

    @classmethod
    def get_instance(cls) -> VoiceManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def scan_voices(self) -> None:
        ensure_voice_dirs()
        self._voices.clear()

        # Built-in voices
        for name, info in BUILTIN_VOICES.items():
            wav_exists = get_voice_wav(name) is not None
            txt_exists = get_voice_text(name) is not None
            self._voices[name] = {
                "name": name,
                "language": info["language"],
                "gender": info["gender"],
                "description": info["description"],
                "custom": False,
                "available": wav_exists and txt_exists,
            }

        # Custom voices: scan for .wav files
        for wav in CUSTOM_VOICES_DIR.glob("*.wav"):
            name = wav.stem
            if name not in self._voices:
                txt_exists = get_voice_text(name) is not None
                self._voices[name] = {
                    "name": name,
                    "language": "unknown",
                    "gender": "unknown",
                    "description": "Custom uploaded voice",
                    "custom": True,
                    "available": txt_exists,
                }

        available = sum(1 for v in self._voices.values() if v.get("available", True))
        logger.info(
            f"Scanned {len(self._voices)} voices ({len(BUILTIN_VOICES)} builtin, {available} available)"
        )

    @property
    def voices(self) -> dict[str, dict]:
        return self._voices

    def voice_exists(self, voice_name: str) -> bool:
        return voice_name in self._voices

    def get_ref_text(self, voice_name: str) -> str:
        txt_path = get_voice_text(voice_name)
        if txt_path is None:
            raise FileNotFoundError(f"No reference text found for voice '{voice_name}'")
        return txt_path.read_text(encoding="utf-8").strip()

    def get_ref_codes(self, voice_name: str, codec_id: str) -> torch.Tensor | None:
        codes_path = get_voice_codes(voice_name, codec_id)
        if codes_path is None:
            return None
        return torch.load(codes_path, map_location="cpu", weights_only=True)

    async def get_or_encode_ref_codes(
        self,
        voice_name: str,
        codec_id: str,
        model_manager: object,
        model_id: str,
    ) -> object:
        codes = self.get_ref_codes(voice_name, codec_id)
        if codes is not None:
            return codes

        wav_path = get_voice_wav(voice_name)
        if wav_path is None:
            raise FileNotFoundError(f"No WAV file found for voice '{voice_name}'")

        logger.info(f"Encoding reference for voice '{voice_name}' with codec '{codec_id}'")
        ref_codes = await model_manager.encode_reference(model_id, str(wav_path))

        # Cache the encoded reference
        custom = is_custom_voice(voice_name)
        save_path = voice_codes_path(voice_name, codec_id, custom=custom)
        torch.save(ref_codes, save_path)
        logger.info(f"Cached reference codes at {save_path}")

        return ref_codes

    def upload_voice(
        self,
        voice_name: str,
        wav_data: bytes,
        ref_text: str,
        language: str = "unknown",
        gender: str = "unknown",
    ) -> Path:
        ensure_voice_dirs()
        wav_path = CUSTOM_VOICES_DIR / f"{voice_name}.wav"
        txt_path = CUSTOM_VOICES_DIR / f"{voice_name}.txt"

        wav_path.write_bytes(wav_data)
        txt_path.write_text(ref_text, encoding="utf-8")

        self._voices[voice_name] = {
            "name": voice_name,
            "language": language,
            "gender": gender,
            "description": "Custom uploaded voice",
            "custom": True,
            "available": True,
        }

        logger.info(f"Uploaded custom voice '{voice_name}' (lang={language}, gender={gender})")
        return wav_path

    def delete_voice(self, voice_name: str) -> None:
        if voice_name in BUILTIN_VOICES:
            raise ValueError(f"Cannot delete built-in voice '{voice_name}'")

        if voice_name not in self._voices:
            raise ValueError(f"Voice '{voice_name}' not found")

        # Remove all files for this voice
        for pattern in (f"{voice_name}.wav", f"{voice_name}.txt", f"{voice_name}_*.pt"):
            for f in CUSTOM_VOICES_DIR.glob(pattern):
                f.unlink()

        self._voices.pop(voice_name, None)
        logger.info(f"Deleted custom voice '{voice_name}'")
