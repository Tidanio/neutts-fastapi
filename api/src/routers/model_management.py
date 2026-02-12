from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.src.core.model_config import BACKBONE_MODELS, CODEC_MODELS, get_backbone_info
from api.src.inference.model_manager import ModelLoadingTask, ModelManager
from api.src.structures.schemas import (
    LoadedModelInfo,
    LoadedModelsResponse,
    LoadModelRequest,
    ModelLoadTaskResponse,
    ModelRegistryResponse,
    RegistryModelInfo,
    SwitchDeviceRequest,
    UnloadModelResponse,
    make_error,
)

router = APIRouter(prefix="/v1/models", tags=["Model Management"])


def _task_to_response(task: ModelLoadingTask) -> ModelLoadTaskResponse:
    elapsed = 0.0
    if task.started_at > 0:
        end = task.completed_at if task.completed_at > 0 else time.time()
        elapsed = round(end - task.started_at, 2)
    return ModelLoadTaskResponse(
        task_id=task.task_id,
        model_id=task.model_id,
        status=task.status.value,
        progress_message=task.progress_message,
        error_message=task.error_message,
        elapsed_seconds=elapsed,
    )


@router.post("/load", response_model=ModelLoadTaskResponse)
async def load_model(request: LoadModelRequest) -> ModelLoadTaskResponse:
    """Start loading a model (non-blocking). Returns a task for polling."""
    model_manager = ModelManager.get_instance()
    info = get_backbone_info(request.model_id)

    if info is None:
        raise HTTPException(
            status_code=400,
            detail=make_error(
                f"Unknown model '{request.model_id}'. "
                f"Available: {list(BACKBONE_MODELS.keys())}"
            ),
        )

    try:
        task = await model_manager.load_model_async(
            model_id=request.model_id,
            codec_id=request.codec,
            backbone_device=request.backbone_device,
            codec_device=request.codec_device,
        )
        # Cleanup old tasks opportunistically
        model_manager.cleanup_old_tasks()
        return _task_to_response(task)
    except Exception as e:
        logger.error(f"Failed to start loading model {request.model_id}: {e}")
        raise HTTPException(status_code=500, detail=make_error(str(e), "server_error", 500))


@router.get("/load/{task_id}", response_model=ModelLoadTaskResponse)
async def get_load_status(task_id: str) -> ModelLoadTaskResponse:
    """Poll the status of a model loading task."""
    model_manager = ModelManager.get_instance()
    task = model_manager.get_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=make_error(f"Task '{task_id}' not found"),
        )

    return _task_to_response(task)


@router.get("/loaded", response_model=LoadedModelsResponse)
async def get_loaded_models() -> LoadedModelsResponse:
    """List all loaded models with device details."""
    model_manager = ModelManager.get_instance()
    models = []

    for model_id, loaded in model_manager.loaded_models.items():
        info = get_backbone_info(model_id)
        models.append(LoadedModelInfo(
            model_id=model_id,
            codec=loaded.codec_id,
            backbone_device=loaded.backbone_device,
            codec_device=loaded.codec_device,
            language=info.language if info else None,
            backend=info.backend.value if info else None,
            supports_streaming=info.supports_streaming if info else False,
        ))

    return LoadedModelsResponse(models=models)


@router.post("/{model_id}/switch-device", response_model=ModelLoadTaskResponse)
async def switch_device(model_id: str, request: SwitchDeviceRequest) -> ModelLoadTaskResponse:
    """Switch a loaded model to a different device (CPU <-> GPU)."""
    model_manager = ModelManager.get_instance()

    try:
        task = await model_manager.switch_device(
            model_id=model_id,
            backbone_device=request.backbone_device,
            codec_device=request.codec_device,
        )
        return _task_to_response(task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=make_error(str(e)))
    except Exception as e:
        logger.error(f"Failed to switch device for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=make_error(str(e), "server_error", 500))


@router.delete("/{model_id}", response_model=UnloadModelResponse)
async def unload_model(model_id: str) -> UnloadModelResponse:
    """Unload a model from memory."""
    model_manager = ModelManager.get_instance()

    try:
        await model_manager.unload_model(model_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=make_error(str(e)))

    return UnloadModelResponse(model_id=model_id, status="unloaded")


@router.get("/registry", response_model=ModelRegistryResponse)
async def get_registry() -> ModelRegistryResponse:
    """List all available models (not just loaded ones)."""
    model_manager = ModelManager.get_instance()

    backbones = [
        RegistryModelInfo(
            model_id=info.model_id,
            repo=info.repo,
            language=info.language,
            backend=info.backend.value,
            supports_streaming=info.supports_streaming,
            description=info.description,
            loaded=model_manager.is_loaded(info.model_id),
        )
        for info in BACKBONE_MODELS.values()
    ]

    codecs = [
        {
            "codec_id": c.codec_id,
            "repo": c.repo,
            "type": c.codec_type,
            "description": c.description,
        }
        for c in CODEC_MODELS.values()
    ]

    return ModelRegistryResponse(backbones=backbones, codecs=codecs)
