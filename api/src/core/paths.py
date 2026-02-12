from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
API_ROOT = PROJECT_ROOT / "api"
SRC_ROOT = API_ROOT / "src"
VOICES_DIR = SRC_ROOT / "voices"
BUILTIN_VOICES_DIR = VOICES_DIR / "builtin"
CUSTOM_VOICES_DIR = VOICES_DIR / "custom"


def ensure_voice_dirs() -> None:
    BUILTIN_VOICES_DIR.mkdir(parents=True, exist_ok=True)
    CUSTOM_VOICES_DIR.mkdir(parents=True, exist_ok=True)


def get_voice_wav(voice_name: str) -> Path | None:
    for base in (BUILTIN_VOICES_DIR, CUSTOM_VOICES_DIR):
        wav = base / f"{voice_name}.wav"
        if wav.exists():
            return wav
    return None


def get_voice_text(voice_name: str) -> Path | None:
    for base in (BUILTIN_VOICES_DIR, CUSTOM_VOICES_DIR):
        txt = base / f"{voice_name}.txt"
        if txt.exists():
            return txt
    return None


def get_voice_codes(voice_name: str, codec_id: str) -> Path | None:
    codec_suffix = codec_id.replace("/", "_")
    for base in (BUILTIN_VOICES_DIR, CUSTOM_VOICES_DIR):
        pt = base / f"{voice_name}_{codec_suffix}.pt"
        if pt.exists():
            return pt
    return None


def voice_codes_path(voice_name: str, codec_id: str, custom: bool = False) -> Path:
    codec_suffix = codec_id.replace("/", "_")
    base = CUSTOM_VOICES_DIR if custom else BUILTIN_VOICES_DIR
    return base / f"{voice_name}_{codec_suffix}.pt"


def is_custom_voice(voice_name: str) -> bool:
    return (CUSTOM_VOICES_DIR / f"{voice_name}.wav").exists()
