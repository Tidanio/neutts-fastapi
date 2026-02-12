from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BackendType(str, Enum):
    TORCH = "torch"
    GGUF = "gguf"
    ONNX = "onnx"


@dataclass(frozen=True)
class BackboneModelInfo:
    model_id: str
    repo: str
    language: str
    backend: BackendType
    supports_streaming: bool
    description: str


@dataclass(frozen=True)
class CodecModelInfo:
    codec_id: str
    repo: str
    codec_type: str
    description: str


BACKBONE_MODELS: dict[str, BackboneModelInfo] = {
    # NeuTTS-Air (English)
    "neutts-air": BackboneModelInfo(
        model_id="neutts-air",
        repo="neuphonic/neutts-air",
        language="en-us",
        backend=BackendType.TORCH,
        supports_streaming=False,
        description="NeuTTS Air ~748M params, PyTorch",
    ),
    "neutts-air-q4-gguf": BackboneModelInfo(
        model_id="neutts-air-q4-gguf",
        repo="neuphonic/neutts-air-q4-gguf",
        language="en-us",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Air Q4 quantized, GGUF",
    ),
    "neutts-air-q8-gguf": BackboneModelInfo(
        model_id="neutts-air-q8-gguf",
        repo="neuphonic/neutts-air-q8-gguf",
        language="en-us",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Air Q8 quantized, GGUF",
    ),
    "neutts-air-onnx": BackboneModelInfo(
        model_id="neutts-air-onnx",
        repo="neuphonic/neutts-air-onnx",
        language="en-us",
        backend=BackendType.ONNX,
        supports_streaming=False,
        description="NeuTTS Air ONNX runtime",
    ),
    # NeuTTS-Nano (English)
    "neutts-nano": BackboneModelInfo(
        model_id="neutts-nano",
        repo="neuphonic/neutts-nano",
        language="en-us",
        backend=BackendType.TORCH,
        supports_streaming=False,
        description="NeuTTS Nano ~120M params, PyTorch",
    ),
    "neutts-nano-q4-gguf": BackboneModelInfo(
        model_id="neutts-nano-q4-gguf",
        repo="neuphonic/neutts-nano-q4-gguf",
        language="en-us",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Nano Q4 quantized, GGUF",
    ),
    "neutts-nano-q8-gguf": BackboneModelInfo(
        model_id="neutts-nano-q8-gguf",
        repo="neuphonic/neutts-nano-q8-gguf",
        language="en-us",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Nano Q8 quantized, GGUF",
    ),
    # NeuTTS-Nano German
    "neutts-nano-german": BackboneModelInfo(
        model_id="neutts-nano-german",
        repo="neuphonic/neutts-nano-german",
        language="de",
        backend=BackendType.TORCH,
        supports_streaming=False,
        description="NeuTTS Nano German, PyTorch",
    ),
    "neutts-nano-german-q4-gguf": BackboneModelInfo(
        model_id="neutts-nano-german-q4-gguf",
        repo="neuphonic/neutts-nano-german-q4-gguf",
        language="de",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Nano German Q4 quantized, GGUF",
    ),
    "neutts-nano-german-q8-gguf": BackboneModelInfo(
        model_id="neutts-nano-german-q8-gguf",
        repo="neuphonic/neutts-nano-german-q8-gguf",
        language="de",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Nano German Q8 quantized, GGUF",
    ),
    # NeuTTS-Nano French
    "neutts-nano-french": BackboneModelInfo(
        model_id="neutts-nano-french",
        repo="neuphonic/neutts-nano-french",
        language="fr-fr",
        backend=BackendType.TORCH,
        supports_streaming=False,
        description="NeuTTS Nano French, PyTorch",
    ),
    "neutts-nano-french-q4-gguf": BackboneModelInfo(
        model_id="neutts-nano-french-q4-gguf",
        repo="neuphonic/neutts-nano-french-q4-gguf",
        language="fr-fr",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Nano French Q4 quantized, GGUF",
    ),
    "neutts-nano-french-q8-gguf": BackboneModelInfo(
        model_id="neutts-nano-french-q8-gguf",
        repo="neuphonic/neutts-nano-french-q8-gguf",
        language="fr-fr",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Nano French Q8 quantized, GGUF",
    ),
    # NeuTTS-Nano Spanish
    "neutts-nano-spanish": BackboneModelInfo(
        model_id="neutts-nano-spanish",
        repo="neuphonic/neutts-nano-spanish",
        language="es",
        backend=BackendType.TORCH,
        supports_streaming=False,
        description="NeuTTS Nano Spanish, PyTorch",
    ),
    "neutts-nano-spanish-q4-gguf": BackboneModelInfo(
        model_id="neutts-nano-spanish-q4-gguf",
        repo="neuphonic/neutts-nano-spanish-q4-gguf",
        language="es",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Nano Spanish Q4 quantized, GGUF",
    ),
    "neutts-nano-spanish-q8-gguf": BackboneModelInfo(
        model_id="neutts-nano-spanish-q8-gguf",
        repo="neuphonic/neutts-nano-spanish-q8-gguf",
        language="es",
        backend=BackendType.GGUF,
        supports_streaming=True,
        description="NeuTTS Nano Spanish Q8 quantized, GGUF",
    ),
}

CODEC_MODELS: dict[str, CodecModelInfo] = {
    "neuphonic/neucodec": CodecModelInfo(
        codec_id="neuphonic/neucodec",
        repo="neuphonic/neucodec",
        codec_type="pytorch",
        description="NeuCodec PyTorch (cpu/cuda)",
    ),
    "neuphonic/distill-neucodec": CodecModelInfo(
        codec_id="neuphonic/distill-neucodec",
        repo="neuphonic/distill-neucodec",
        codec_type="pytorch",
        description="Distilled NeuCodec PyTorch (cpu/cuda)",
    ),
    "neuphonic/neucodec-onnx-decoder": CodecModelInfo(
        codec_id="neuphonic/neucodec-onnx-decoder",
        repo="neuphonic/neucodec-onnx-decoder",
        codec_type="onnx",
        description="NeuCodec ONNX decoder (cpu)",
    ),
    "neuphonic/neucodec-onnx-decoder-int8": CodecModelInfo(
        codec_id="neuphonic/neucodec-onnx-decoder-int8",
        repo="neuphonic/neucodec-onnx-decoder-int8",
        codec_type="onnx_int8",
        description="NeuCodec ONNX INT8 decoder (cpu)",
    ),
}

BUILTIN_VOICES: dict[str, dict] = {
    "dave": {"language": "en-us", "gender": "male", "description": "English male voice"},
    "jo": {"language": "en-us", "gender": "female", "description": "English female voice"},
    "greta": {"language": "de", "gender": "female", "description": "German female voice"},
    "hans": {"language": "de", "gender": "male", "description": "German male voice"},
    "mateo": {"language": "es", "gender": "male", "description": "Spanish male voice"},
    "elena": {"language": "es", "gender": "female", "description": "Spanish female voice"},
    "juliette": {"language": "fr-fr", "gender": "female", "description": "French female voice"},
    "pierre": {"language": "fr-fr", "gender": "male", "description": "French male voice"},
}


def get_backbone_info(model_id: str) -> BackboneModelInfo | None:
    return BACKBONE_MODELS.get(model_id)


def get_codec_info(codec_id: str) -> CodecModelInfo | None:
    return CODEC_MODELS.get(codec_id)


def get_voice_language(voice_name: str) -> str | None:
    info = BUILTIN_VOICES.get(voice_name)
    return info["language"] if info else None
