from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# --- OpenAI-compatible Request ---

class OpenAISpeechRequest(BaseModel):
    model: str = "neutts-nano-q4-gguf"
    input: str = Field(..., min_length=1, max_length=10000)
    voice: str = "jo"
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "mp3"
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    stream: bool = False


# --- OpenAI-compatible Responses ---

class VoiceInfo(BaseModel):
    voice_id: str
    name: str
    language: str
    gender: str
    custom: bool = False
    available: bool = True
    preview_url: str | None = None


class VoiceListResponse(BaseModel):
    voices: list[VoiceInfo]


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "neuphonic"
    language: str | None = None
    backend: str | None = None
    supports_streaming: bool = False
    backbone_device: str | None = None
    codec_device: str | None = None


class ModelListResponse(BaseModel):
    object: str = "list"
    data: list[ModelInfo]


class ModelDetailResponse(ModelInfo):
    loaded: bool = False
    codec: str | None = None


# --- Model Management ---

class LoadModelRequest(BaseModel):
    model_id: str
    codec: str | None = None
    backbone_device: str | None = None
    codec_device: str | None = None


class UnloadModelResponse(BaseModel):
    model_id: str
    status: str = "unloaded"


class ModelLoadTaskResponse(BaseModel):
    task_id: str
    model_id: str
    status: str
    progress_message: str = ""
    error_message: str = ""
    elapsed_seconds: float = 0.0


class SwitchDeviceRequest(BaseModel):
    backbone_device: str | None = None
    codec_device: str | None = None


class LoadedModelInfo(BaseModel):
    model_id: str
    codec: str
    backbone_device: str
    codec_device: str
    language: str | None = None
    backend: str | None = None
    supports_streaming: bool = False


class LoadedModelsResponse(BaseModel):
    models: list[LoadedModelInfo]


class RegistryModelInfo(BaseModel):
    model_id: str
    repo: str
    language: str
    backend: str
    supports_streaming: bool
    description: str
    loaded: bool = False


class ModelRegistryResponse(BaseModel):
    backbones: list[RegistryModelInfo]
    codecs: list[dict]


# --- Voice Management ---

class VoiceEncodeRequest(BaseModel):
    codec: str | None = None


class VoiceUploadResponse(BaseModel):
    voice_id: str
    status: str = "uploaded"
    message: str = ""
    language: str = "unknown"
    gender: str = "unknown"


class VoiceDeleteResponse(BaseModel):
    voice_id: str
    status: str = "deleted"


class VoiceEncodeResponse(BaseModel):
    voice_id: str
    codec: str
    status: str = "encoded"


# --- Health & Debug ---

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    models_loaded: int = 0


class SystemDebugResponse(BaseModel):
    cpu_count: int
    cpu_percent: float
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    gpu_available: bool
    gpu_info: list[dict] | None = None
    torch_version: str | None = None
    cuda_version: str | None = None
    cuda_driver_version: str | None = None
    gpu_detected_but_unusable: bool = False
    gpu_fix_instructions: str | None = None
    models_loaded: list[str]
    voices_available: int


# --- Error ---

class ErrorResponse(BaseModel):
    error: dict


def make_error(message: str, error_type: str = "invalid_request_error", code: int = 400) -> dict:
    return {
        "error": {
            "message": message,
            "type": error_type,
            "code": code,
        }
    }
