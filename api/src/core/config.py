from __future__ import annotations

import json
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "NEUTTS_", "env_file": ".env", "extra": "ignore"}

    # Server
    host: str = "0.0.0.0"
    port: int = 8880

    # Models
    default_models: str = "neutts-nano-q4-gguf"
    default_codec: str = "neuphonic/neucodec-onnx-decoder"
    default_backbone_device: Literal["auto", "cpu", "cuda"] = "auto"
    default_codec_device: Literal["cpu", "cuda"] = "cpu"

    # Voice
    default_voice: str = "jo"

    # Audio
    sample_rate: int = 24000
    default_response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3"

    # CORS
    cors_enabled: bool = True
    cors_origins: str = '["*"]'

    # Logging
    log_level: str = "INFO"

    # Performance
    max_inference_workers: int = 4

    # Voice Upload
    allow_voice_upload: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list) -> str:
        if isinstance(v, list):
            return json.dumps(v)
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return json.loads(self.cors_origins)

    @property
    def default_models_list(self) -> list[str]:
        return [m.strip() for m in self.default_models.split(",") if m.strip()]

    @property
    def resolved_backbone_device(self) -> str:
        if self.default_backbone_device == "auto":
            try:
                import torch

                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return self.default_backbone_device


settings = Settings()
