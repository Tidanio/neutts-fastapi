from __future__ import annotations

import base64
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from api.src.core.config import settings
from api.src.inference.model_manager import ModelManager
from api.src.inference.voice_manager import VoiceManager
from api.src.services.streaming_audio_writer import StreamingAudioWriter
from api.src.structures.websocket_schemas import (
    WSResponseMessage,
    WSStartMessage,
)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/v1/audio/speech/stream")
async def websocket_tts(ws: WebSocket) -> None:
    """WebSocket endpoint for real-time TTS streaming.

    Protocol:
    1. Client sends: {"type": "start", "model": "...", "voice": "...", "response_format": "pcm"}
    2. Client sends: {"type": "text", "text": "Hello world"}
    3. Server streams: {"type": "audio", "data": "<base64>", "format": "pcm"}
    4. Server sends: {"type": "done"}
    5. Client sends: {"type": "stop"} or more text messages
    """
    await ws.accept()
    logger.info("WebSocket connection accepted")

    model_manager = ModelManager.get_instance()
    voice_manager = VoiceManager.get_instance()

    session_config: WSStartMessage | None = None

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
                continue

            if msg_type == "start":
                session_config = WSStartMessage(**msg)

                # Validate model
                if not model_manager.is_loaded(session_config.model):
                    await _send_error(ws, f"Model '{session_config.model}' is not loaded")
                    continue

                if not voice_manager.voice_exists(session_config.voice):
                    await _send_error(ws, f"Voice '{session_config.voice}' not found")
                    continue

                logger.info(
                    f"WS session started: model={session_config.model} "
                    f"voice={session_config.voice} format={session_config.response_format}"
                )
                continue

            if msg_type == "text":
                if session_config is None:
                    await _send_error(ws, "Send a 'start' message first")
                    continue

                text = msg.get("text", "").strip()
                if not text:
                    await _send_error(ws, "Empty text")
                    continue

                await _handle_text(ws, session_config, text, model_manager, voice_manager)

            elif msg_type == "stop":
                logger.info("WS session stopped by client")
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await _send_error(ws, str(e))
        except Exception:
            pass


async def _handle_text(
    ws: WebSocket,
    config: WSStartMessage,
    text: str,
    model_manager: ModelManager,
    voice_manager: VoiceManager,
) -> None:
    loaded = model_manager.loaded_models[config.model]
    ref_codes = await voice_manager.get_or_encode_ref_codes(
        config.voice, loaded.codec_id, model_manager, config.model
    )
    ref_text = voice_manager.get_ref_text(config.voice)

    from api.src.core.model_config import get_backbone_info

    info = get_backbone_info(config.model)
    writer = StreamingAudioWriter(config.response_format, settings.sample_rate)

    try:
        if info and info.supports_streaming:
            async for chunk in model_manager.infer_stream(
                config.model, text, ref_codes, ref_text
            ):
                encoded = writer.write_chunk(chunk)
                if encoded:
                    await ws.send_text(json.dumps({
                        "type": "audio",
                        "data": base64.b64encode(encoded).decode(),
                        "format": config.response_format,
                    }))
        else:
            wav = await model_manager.infer(config.model, text, ref_codes, ref_text)
            encoded = writer.write_chunk(wav)
            if encoded:
                await ws.send_text(json.dumps({
                    "type": "audio",
                    "data": base64.b64encode(encoded).decode(),
                    "format": config.response_format,
                }))

        final = writer.finalize()
        if final:
            await ws.send_text(json.dumps({
                "type": "audio",
                "data": base64.b64encode(final).decode(),
                "format": config.response_format,
            }))

        await ws.send_text(json.dumps({"type": "done"}))

    finally:
        writer.close()


async def _send_error(ws: WebSocket, message: str) -> None:
    await ws.send_text(json.dumps({"type": "error", "message": message}))
