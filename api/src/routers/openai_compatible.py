from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from loguru import logger

from api.src.core.model_config import get_backbone_info
from api.src.inference.model_manager import ModelManager
from api.src.inference.voice_manager import VoiceManager
from api.src.services.streaming_audio_writer import get_content_type
from api.src.services.tts_service import TTSService
from api.src.structures.schemas import (
    ModelDetailResponse,
    ModelInfo,
    ModelListResponse,
    OpenAISpeechRequest,
    VoiceInfo,
    VoiceListResponse,
    make_error,
)

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])


@router.post("/audio/speech")
async def create_speech(request: OpenAISpeechRequest) -> Response:
    """OpenAI-compatible TTS endpoint."""
    model_manager = ModelManager.get_instance()
    voice_manager = VoiceManager.get_instance()
    tts_service = TTSService.get_instance()

    # Validate model
    if not model_manager.is_loaded(request.model):
        raise HTTPException(status_code=400, detail=make_error(
            f"Model '{request.model}' is not loaded. "
            f"Available: {list(model_manager.loaded_models.keys())}"
        ))

    # Validate voice
    if not voice_manager.voice_exists(request.voice):
        raise HTTPException(status_code=400, detail=make_error(
            f"Voice '{request.voice}' not found. "
            f"Available: {list(voice_manager.voices.keys())}"
        ))

    content_type = get_content_type(request.response_format)

    try:
        if request.stream:
            return StreamingResponse(
                tts_service.stream_speech(request),
                media_type=content_type,
                headers={
                    "Content-Type": content_type,
                    "Transfer-Encoding": "chunked",
                },
            )
        else:
            start = time.perf_counter()
            audio_data = await tts_service.generate_speech(request)
            elapsed = time.perf_counter() - start
            logger.info(
                f"TTS: model={request.model} voice={request.voice} "
                f"format={request.response_format} chars={len(request.input)} "
                f"time={elapsed:.2f}s size={len(audio_data)} bytes"
            )
            return Response(
                content=audio_data,
                media_type=content_type,
                headers={"Content-Type": content_type},
            )
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(status_code=500, detail=make_error(str(e), "server_error", 500))


@router.get("/audio/voices", response_model=VoiceListResponse)
async def list_voices() -> VoiceListResponse:
    """List available voices."""
    voice_manager = VoiceManager.get_instance()
    voices = [
        VoiceInfo(
            voice_id=name,
            name=name,
            language=info["language"],
            gender=info["gender"],
            custom=info.get("custom", False),
            available=info.get("available", True),
        )
        for name, info in voice_manager.voices.items()
    ]
    return VoiceListResponse(voices=voices)


@router.get("/models", response_model=ModelListResponse)
async def list_models() -> ModelListResponse:
    """List loaded models (OpenAI-compatible)."""
    model_manager = ModelManager.get_instance()
    models = []
    for model_id, loaded in model_manager.loaded_models.items():
        info = get_backbone_info(model_id)
        models.append(ModelInfo(
            id=model_id,
            language=info.language if info else None,
            backend=info.backend.value if info else None,
            supports_streaming=info.supports_streaming if info else False,
            backbone_device=loaded.backbone_device,
            codec_device=loaded.codec_device,
        ))
    return ModelListResponse(data=models)


@router.get("/models/{model_id}", response_model=ModelDetailResponse)
async def get_model(model_id: str) -> ModelDetailResponse:
    """Get details about a specific model."""
    model_manager = ModelManager.get_instance()
    info = get_backbone_info(model_id)

    if info is None:
        raise HTTPException(status_code=404, detail=make_error(f"Model '{model_id}' not found"))

    loaded = model_manager.loaded_models.get(model_id)
    return ModelDetailResponse(
        id=model_id,
        language=info.language,
        backend=info.backend.value,
        supports_streaming=info.supports_streaming,
        loaded=loaded is not None,
        codec=loaded.codec_id if loaded else None,
    )
