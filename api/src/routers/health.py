from __future__ import annotations

from fastapi import APIRouter

from api.src.inference.model_manager import ModelManager
from api.src.structures.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    model_manager = ModelManager.get_instance()
    return HealthResponse(
        status="ok",
        version="0.1.0",
        models_loaded=len(model_manager.loaded_models),
    )
