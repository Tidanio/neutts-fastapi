from __future__ import annotations

import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from api.src.core.config import settings
from api.src.inference.model_manager import ModelManager
from api.src.inference.voice_manager import VoiceManager
from api.src.services.temp_manager import cleanup_temp

# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("NeuTTS-FastAPI starting up...")

    # Initialize voice manager
    voice_manager = VoiceManager.get_instance()
    voice_manager.scan_voices()

    # GPU startup diagnostics
    try:
        import torch

        torch_cuda_ok = torch.cuda.is_available()
        if not torch_cuda_ok:
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    from api.src.routers.debug import _build_gpu_fix_instructions
                    line = result.stdout.strip().split("\n")[0]
                    parts = [p.strip() for p in line.split(",")]
                    gpu_name = parts[0]
                    driver_ver = parts[1] if len(parts) > 1 else "unknown"
                    fix = _build_gpu_fix_instructions(
                        gpu_name, driver_ver, torch.__version__, torch.version.cuda,
                    )
                    logger.warning(f"GPU detected but unusable! Running on CPU only.\n{fix}")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
    except ImportError:
        pass

    # Load default models
    model_manager = ModelManager.get_instance()
    await model_manager.startup()

    logger.info(
        f"Ready! Models: {list(model_manager.loaded_models.keys())}, "
        f"Voices: {list(voice_manager.voices.keys())}"
    )

    yield

    # Shutdown
    logger.info("Shutting down...")
    await model_manager.shutdown()
    cleanup_temp()
    logger.info("Shutdown complete")


app = FastAPI(
    title="NeuTTS-FastAPI",
    description="OpenAI-compatible Text-to-Speech API powered by NeuTTS",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register routers
from api.src.routers import (
    debug,
    health,
    model_management,
    openai_compatible,
    voice_management,
    websocket,
)

# model_management first so /v1/models/registry is matched before /v1/models/{model_id}
app.include_router(model_management.router)
app.include_router(openai_compatible.router)
app.include_router(voice_management.router)
app.include_router(websocket.router)
app.include_router(health.router)
app.include_router(debug.router)

# Serve Web UI
_static_dir = Path(__file__).parent / "static"


@app.get("/", include_in_schema=False)
async def web_ui():
    return FileResponse(_static_dir / "index.html")


app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.src.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
