from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from loguru import logger

from api.src.core.config import settings
from api.src.inference.model_manager import ModelManager
from api.src.inference.voice_manager import VoiceManager
from api.src.services.audio_utils import validate_reference_audio
from api.src.structures.schemas import (
    VoiceDeleteResponse,
    VoiceEncodeRequest,
    VoiceEncodeResponse,
    VoiceUploadResponse,
    make_error,
)

router = APIRouter(prefix="/v1/audio/voices", tags=["Voice Management"])


@router.post("/upload", response_model=VoiceUploadResponse)
async def upload_voice(
    voice_id: str = Form(...),
    ref_text: str = Form(...),
    audio: UploadFile = File(...),
    language: str = Form("unknown"),
    gender: str = Form("unknown"),
) -> VoiceUploadResponse:
    """Upload a custom voice reference (WAV + transcription text)."""
    if not settings.allow_voice_upload:
        raise HTTPException(status_code=403, detail=make_error("Voice upload is disabled"))

    voice_manager = VoiceManager.get_instance()

    # Check name is valid
    if not voice_id.isalnum() and not all(c.isalnum() or c in "-_" for c in voice_id):
        raise HTTPException(
            status_code=400,
            detail=make_error("Voice ID must be alphanumeric (hyphens/underscores allowed)"),
        )

    if voice_manager.voice_exists(voice_id):
        raise HTTPException(
            status_code=409,
            detail=make_error(f"Voice '{voice_id}' already exists"),
        )

    # Read and validate audio
    wav_data = await audio.read()
    try:
        props = validate_reference_audio(wav_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=make_error(str(e)))

    voice_manager.upload_voice(voice_id, wav_data, ref_text, language=language, gender=gender)

    return VoiceUploadResponse(
        voice_id=voice_id,
        status="uploaded",
        message=f"Voice uploaded ({props['duration']:.1f}s, {props['sample_rate']}Hz)",
        language=language,
        gender=gender,
    )


@router.post("/{voice_id}/encode", response_model=VoiceEncodeResponse)
async def encode_voice(voice_id: str, request: VoiceEncodeRequest | None = None) -> VoiceEncodeResponse:
    """Pre-encode a voice reference for a specific codec."""
    voice_manager = VoiceManager.get_instance()
    model_manager = ModelManager.get_instance()

    if not voice_manager.voice_exists(voice_id):
        raise HTTPException(status_code=404, detail=make_error(f"Voice '{voice_id}' not found"))

    # Use first loaded model to encode
    if not model_manager.loaded_models:
        raise HTTPException(
            status_code=400,
            detail=make_error("No models loaded. Load a model first."),
        )

    model_id = next(iter(model_manager.loaded_models))
    loaded = model_manager.loaded_models[model_id]
    codec = (request.codec if request and request.codec else loaded.codec_id)

    try:
        await voice_manager.get_or_encode_ref_codes(
            voice_id, codec, model_manager, model_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=make_error(str(e), "server_error", 500))

    return VoiceEncodeResponse(voice_id=voice_id, codec=codec, status="encoded")


@router.delete("/{voice_id}", response_model=VoiceDeleteResponse)
async def delete_voice(voice_id: str) -> VoiceDeleteResponse:
    """Delete a custom voice."""
    voice_manager = VoiceManager.get_instance()

    try:
        voice_manager.delete_voice(voice_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=make_error(str(e)))

    return VoiceDeleteResponse(voice_id=voice_id, status="deleted")
