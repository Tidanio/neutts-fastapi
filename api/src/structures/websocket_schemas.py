from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WSMessage(BaseModel):
    type: Literal["start", "text", "stop", "ping"]


class WSStartMessage(WSMessage):
    type: Literal["start"] = "start"
    model: str = "neutts-nano-q4-gguf"
    voice: str = "jo"
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "pcm"
    sample_rate: int = 24000


class WSTextMessage(WSMessage):
    type: Literal["text"] = "text"
    text: str = Field(..., min_length=1)


class WSStopMessage(WSMessage):
    type: Literal["stop"] = "stop"


class WSPingMessage(WSMessage):
    type: Literal["ping"] = "ping"


class WSResponseMessage(BaseModel):
    type: Literal["audio", "error", "done", "pong"]
    data: str | None = None
    message: str | None = None
    format: str | None = None
