# NeuTTS-FastAPI

OpenAI-compatible Text-to-Speech API server powered by [NeuTTS](https://github.com/neuphonic/neuTTS) from [Neuphonic](https://www.neuphonic.com/).

Drop-in replacement for the OpenAI TTS API with support for multiple languages, custom voice cloning, real-time streaming, and a built-in web UI.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)

---

## Features

- **OpenAI-Compatible API** - Works with the official OpenAI Python SDK and any OpenAI TTS client
- **4 Languages** - English, German, French, Spanish with dedicated models per language
- **8 Built-in Voices** - 2 voices per language (male + female)
- **Custom Voice Cloning** - Upload a WAV reference + transcription or record directly in the browser
- **Real-time Streaming** - HTTP chunked streaming and WebSocket support
- **Multiple Output Formats** - MP3, WAV, Opus, AAC, FLAC, PCM
- **GPU Acceleration** - CUDA support with automatic detection (including RTX 50xx Blackwell)
- **Dynamic Model Management** - Load/unload models at runtime, switch between CPU and GPU
- **Built-in Web UI** - Generate speech, manage voices and models from the browser
- **Docker Ready** - CPU and GPU Docker images with Compose files
- **One-Click Launchers** - Start scripts for Windows, macOS, and Linux

---

## Quick Start

### One-Click Launch

Download and run the appropriate script for your OS:

| OS | Script | How to run |
|---|---|---|
| **Windows** | `start.bat` | Double-click in Explorer |
| **macOS** | `start.command` | Double-click in Finder |
| **Linux** | `start.sh` | `chmod +x start.sh && ./start.sh` |

The script will:
1. Check for Python 3.10+ and espeak-ng
2. Create a virtual environment
3. Detect your GPU and install the matching PyTorch version
4. Start the server at **http://localhost:8880**

Messages are displayed in English, German, French, or Spanish based on your system language.

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/rbaluyos/neutts-fastapi.git
cd neutts-fastapi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install (CPU)
pip install -e ".[cpu]"

# Or install (GPU - NVIDIA CUDA)
pip install -e ".[gpu]" --index-url https://download.pytorch.org/whl/cu124 --extra-index-url https://pypi.org/simple/

# RTX 50xx (Blackwell) needs CUDA 12.8:
# pip install -e ".[gpu]" --index-url https://download.pytorch.org/whl/cu128 --extra-index-url https://pypi.org/simple/

# Start the server
python -m uvicorn api.src.main:app --host 0.0.0.0 --port 8880
```

> **Requirement:** [espeak-ng](https://github.com/espeak-ng/espeak-ng) must be installed for phonemization.
> Windows: `winget install espeak-ng.espeak-ng`
> macOS: `brew install espeak-ng`
> Ubuntu/Debian: `sudo apt install espeak-ng`

---

## Docker

### CPU

```bash
cd docker/cpu
docker compose up --build
```

### GPU (NVIDIA)

```bash
cd docker/gpu
docker compose up --build
```

Requires the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

### Environment Variables

Copy `.env.example` to `.env` and adjust as needed:

| Variable | Default | Description |
|---|---|---|
| `NEUTTS_HOST` | `0.0.0.0` | Bind address |
| `NEUTTS_PORT` | `8880` | Server port |
| `NEUTTS_DEFAULT_MODELS` | `neutts-nano-q4-gguf` | Models to load on startup (comma-separated) |
| `NEUTTS_DEFAULT_CODEC` | `neuphonic/neucodec-onnx-decoder` | Audio codec model |
| `NEUTTS_DEFAULT_BACKBONE_DEVICE` | `auto` | `auto`, `cpu`, or `cuda` |
| `NEUTTS_DEFAULT_CODEC_DEVICE` | `cpu` | `cpu` or `cuda` |
| `NEUTTS_DEFAULT_VOICE` | `jo` | Default voice for TTS |
| `NEUTTS_SAMPLE_RATE` | `24000` | Output sample rate (Hz) |
| `NEUTTS_DEFAULT_RESPONSE_FORMAT` | `mp3` | `mp3`, `wav`, `opus`, `aac`, `flac`, `pcm` |
| `NEUTTS_LOG_LEVEL` | `INFO` | Logging level |
| `NEUTTS_ALLOW_VOICE_UPLOAD` | `true` | Enable custom voice uploads |
| `NEUTTS_MAX_INFERENCE_WORKERS` | `4` | Concurrent inference limit |

---

## Available Models

### TTS Models

| Model | Language | Parameters | Format | Streaming |
|---|---|---|---|---|
| `neutts-air` | English | ~748M | PyTorch | No |
| `neutts-air-q4-gguf` | English | ~748M | GGUF Q4 | Yes |
| `neutts-air-q8-gguf` | English | ~748M | GGUF Q8 | Yes |
| `neutts-air-onnx` | English | ~748M | ONNX | No |
| `neutts-nano` | English | ~120M | PyTorch | No |
| `neutts-nano-q4-gguf` | English | ~120M | GGUF Q4 | Yes |
| `neutts-nano-q8-gguf` | English | ~120M | GGUF Q8 | Yes |
| `neutts-nano-german` | German | ~120M | PyTorch | No |
| `neutts-nano-german-q4-gguf` | German | ~120M | GGUF Q4 | Yes |
| `neutts-nano-german-q8-gguf` | German | ~120M | GGUF Q8 | Yes |
| `neutts-nano-french` | French | ~120M | PyTorch | No |
| `neutts-nano-french-q4-gguf` | French | ~120M | GGUF Q4 | Yes |
| `neutts-nano-french-q8-gguf` | French | ~120M | GGUF Q8 | Yes |
| `neutts-nano-spanish` | Spanish | ~120M | PyTorch | No |
| `neutts-nano-spanish-q4-gguf` | Spanish | ~120M | GGUF Q4 | Yes |
| `neutts-nano-spanish-q8-gguf` | Spanish | ~120M | GGUF Q8 | Yes |

### Codec Models

| Model | Format | Device |
|---|---|---|
| `neuphonic/neucodec` | PyTorch | cpu, cuda |
| `neuphonic/distill-neucodec` | PyTorch (distilled) | cpu, cuda |
| `neuphonic/neucodec-onnx-decoder` | ONNX | cpu |
| `neuphonic/neucodec-onnx-decoder-int8` | ONNX INT8 | cpu |

### Built-in Voices

| Voice | Language | Gender |
|---|---|---|
| `jo` | English | Female |
| `dave` | English | Male |
| `greta` | German | Female |
| `hans` | German | Male |
| `juliette` | French | Female |
| `pierre` | French | Male |
| `mateo` | Spanish | Male |
| `elena` | Spanish | Female |

---

## API Reference

### OpenAI-Compatible Endpoints

#### Generate Speech

```
POST /v1/audio/speech
```

```json
{
  "model": "neutts-nano-q4-gguf",
  "input": "Hello world!",
  "voice": "jo",
  "response_format": "mp3",
  "stream": false
}
```

#### List Voices

```
GET /v1/audio/voices
```

#### List Models

```
GET /v1/models
```

### Voice Management

```
POST   /v1/audio/voices/upload          # Upload custom voice (multipart form)
POST   /v1/audio/voices/{id}/encode     # Pre-encode voice for codec
DELETE /v1/audio/voices/{id}            # Delete custom voice
```

### Model Management

```
POST   /v1/models/load                  # Load a model (async, returns task ID)
GET    /v1/models/load/{task_id}        # Poll loading status
GET    /v1/models/loaded                # List loaded models with details
GET    /v1/models/registry              # List all available models
POST   /v1/models/{id}/switch-device    # Switch model between CPU/GPU
DELETE /v1/models/{id}                  # Unload model from memory
```

### WebSocket Streaming

```
WS /v1/audio/speech/stream
```

Protocol: `start` -> `text` -> receive `audio` chunks -> `done` -> `stop`

### Health & Debug

```
GET /health           # Health check
GET /debug/system     # System diagnostics (CPU, RAM, GPU, models, voices)
```

---

## Usage Examples

### OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8880/v1",
    api_key="not-needed",
)

response = client.audio.speech.create(
    model="neutts-nano-q4-gguf",
    voice="jo",
    input="Hello! This is NeuTTS.",
)
response.stream_to_file("output.mp3")
```

### HTTP Streaming

```python
import httpx

payload = {
    "model": "neutts-nano-q4-gguf",
    "input": "Streaming audio in real-time.",
    "voice": "jo",
    "response_format": "mp3",
    "stream": True,
}

with httpx.stream("POST", "http://localhost:8880/v1/audio/speech", json=payload) as r:
    with open("output.mp3", "wb") as f:
        for chunk in r.iter_bytes():
            f.write(chunk)
```

### WebSocket

```python
import asyncio, json, base64, websockets

async def stream_tts():
    async with websockets.connect("ws://localhost:8880/v1/audio/speech/stream") as ws:
        await ws.send(json.dumps({
            "type": "start", "model": "neutts-nano-q4-gguf",
            "voice": "jo", "response_format": "pcm",
        }))
        await ws.send(json.dumps({
            "type": "text", "text": "Real-time streaming!",
        }))
        audio = b""
        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == "audio":
                audio += base64.b64decode(msg["data"])
            elif msg["type"] == "done":
                break
        await ws.send(json.dumps({"type": "stop"}))
        return audio

asyncio.run(stream_tts())
```

### cURL

```bash
curl -X POST http://localhost:8880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"neutts-nano-q4-gguf","input":"Hello world!","voice":"jo"}' \
  --output output.mp3
```

### Custom Voice Upload

```bash
curl -X POST http://localhost:8880/v1/audio/voices/upload \
  -F "voice_id=my-voice" \
  -F "ref_text=This is the exact transcription of the audio." \
  -F "language=en-us" \
  -F "gender=female" \
  -F "audio=@reference.wav"
```

---

## Web UI

Open **http://localhost:8880** in your browser for the built-in interface:

- Text-to-speech generation with all voices and models
- Voice cloning via file upload or browser microphone recording
- Model loading/unloading and CPU/GPU device switching
- System diagnostics and GPU status

---

## Project Structure

```
neutts-fastapi/
├── api/src/
│   ├── main.py                  # FastAPI application
│   ├── core/
│   │   ├── config.py            # Settings (env vars)
│   │   ├── model_config.py      # Model registry & builtin voices
│   │   └── paths.py             # Path utilities
│   ├── inference/
│   │   ├── model_manager.py     # Model lifecycle management
│   │   ├── voice_manager.py     # Voice loading & encoding
│   │   └── text_chunker.py      # Text segmentation
│   ├── routers/                 # API endpoints
│   ├── services/                # TTS engine, audio processing
│   ├── structures/              # Pydantic schemas
│   ├── static/                  # Web UI
│   └── voices/
│       ├── builtin/             # Reference audio + transcriptions
│       └── custom/              # User-uploaded voices
├── docker/
│   ├── cpu/                     # CPU Docker setup
│   ├── gpu/                     # GPU Docker setup (CUDA 12.8)
│   └── scripts/                 # Model download scripts
├── examples/                    # Client examples (Python)
├── tests/                       # pytest test suite
├── start.bat                    # Windows one-click launcher
├── start.sh                     # Linux/macOS one-click launcher
├── start.command                # macOS Finder launcher
├── pyproject.toml               # Package config
└── .env.example                 # Configuration template
```

---

## References & Credits

- **[NeuTTS](https://github.com/neuphonic/neuTTS)** - The underlying text-to-speech engine by Neuphonic
- **[Neuphonic](https://www.neuphonic.com/)** - Creator of the NeuTTS models and NeuCodec
- **[espeak-ng](https://github.com/espeak-ng/espeak-ng)** - Phonemizer backend for text processing
- **[FastAPI](https://fastapi.tiangolo.com/)** - Web framework
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)** / **[llama-cpp-python](https://github.com/abetlen/llama-cpp-python)** - GGUF model inference
- **[ONNX Runtime](https://onnxruntime.ai/)** - ONNX model inference

---

## License

[MIT](LICENSE)
