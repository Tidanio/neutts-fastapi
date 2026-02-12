from __future__ import annotations

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator

import numpy as np
from loguru import logger

from api.src.core.config import settings
from api.src.core.model_config import (
    BACKBONE_MODELS,
    BackendType,
    get_backbone_info,
)


class ModelLoadStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


@dataclass
class ModelLoadingTask:
    task_id: str
    model_id: str
    status: ModelLoadStatus = ModelLoadStatus.PENDING
    progress_message: str = ""
    error_message: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0


@dataclass
class LoadedModel:
    model_id: str
    codec_id: str
    tts_instance: object  # NeuTTS instance
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    backbone_device: str = "cpu"
    codec_device: str = "cpu"


class ModelManager:
    _instance: ModelManager | None = None

    def __init__(self) -> None:
        self._models: dict[str, LoadedModel] = {}
        self._loading_tasks: dict[str, ModelLoadingTask] = {}
        self._executor = ThreadPoolExecutor(max_workers=settings.max_inference_workers)

    @classmethod
    def get_instance(cls) -> ModelManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def loaded_models(self) -> dict[str, LoadedModel]:
        return self._models

    @property
    def loading_tasks(self) -> dict[str, ModelLoadingTask]:
        return self._loading_tasks

    def is_loaded(self, model_id: str) -> bool:
        return model_id in self._models

    def get_task(self, task_id: str) -> ModelLoadingTask | None:
        return self._loading_tasks.get(task_id)

    async def load_model_async(
        self,
        model_id: str,
        codec_id: str | None = None,
        backbone_device: str | None = None,
        codec_device: str | None = None,
    ) -> ModelLoadingTask:
        """Start loading a model in the background. Returns a task for polling."""
        # Already loaded -> return READY task immediately
        if model_id in self._models:
            task = ModelLoadingTask(
                task_id=str(uuid.uuid4()),
                model_id=model_id,
                status=ModelLoadStatus.READY,
                progress_message="Already loaded",
                started_at=time.time(),
                completed_at=time.time(),
            )
            self._loading_tasks[task.task_id] = task
            return task

        # Already loading -> return existing task
        for task in self._loading_tasks.values():
            if task.model_id == model_id and task.status in (
                ModelLoadStatus.PENDING,
                ModelLoadStatus.DOWNLOADING,
                ModelLoadStatus.LOADING,
            ):
                return task

        info = get_backbone_info(model_id)
        if info is None:
            raise ValueError(f"Unknown model: {model_id}. Available: {list(BACKBONE_MODELS.keys())}")

        task = ModelLoadingTask(
            task_id=str(uuid.uuid4()),
            model_id=model_id,
            status=ModelLoadStatus.PENDING,
            progress_message="Queued",
            started_at=time.time(),
        )
        self._loading_tasks[task.task_id] = task

        asyncio.ensure_future(
            self._background_load(task, codec_id, backbone_device, codec_device)
        )
        return task

    async def _background_load(
        self,
        task: ModelLoadingTask,
        codec_id: str | None,
        backbone_device: str | None,
        codec_device: str | None,
    ) -> None:
        """Background coroutine that loads a model and updates task status."""
        try:
            task.status = ModelLoadStatus.DOWNLOADING
            task.progress_message = "Downloading / checking cache..."

            info = get_backbone_info(task.model_id)
            if info is None:
                raise ValueError(f"Unknown model: {task.model_id}")

            codec = codec_id or settings.default_codec
            bb_device = backbone_device or settings.resolved_backbone_device
            cc_device = codec_device or settings.default_codec_device

            # GGUF models only support CPU (llama.cpp limitation)
            if info.backend == BackendType.GGUF:
                bb_device = "cpu"

            logger.info(
                f"[Task {task.task_id[:8]}] Loading {task.model_id} "
                f"(backbone_device={bb_device}, codec_device={cc_device})"
            )

            # Schedule status transition after 3s (heuristic for download vs load)
            async def _mark_loading() -> None:
                await asyncio.sleep(3)
                if task.status == ModelLoadStatus.DOWNLOADING:
                    task.status = ModelLoadStatus.LOADING
                    task.progress_message = "Initializing model..."

            timer_task = asyncio.ensure_future(_mark_loading())

            loop = asyncio.get_event_loop()
            tts = await loop.run_in_executor(
                self._executor,
                self._create_tts_instance,
                info.repo,
                codec,
                bb_device,
                cc_device,
            )

            timer_task.cancel()

            loaded = LoadedModel(
                model_id=task.model_id,
                codec_id=codec,
                tts_instance=tts,
                backbone_device=bb_device,
                codec_device=cc_device,
            )
            self._models[task.model_id] = loaded

            task.status = ModelLoadStatus.READY
            task.progress_message = "Model ready"
            task.completed_at = time.time()
            logger.info(f"[Task {task.task_id[:8]}] {task.model_id} loaded successfully")

        except Exception as e:
            task.status = ModelLoadStatus.ERROR
            task.error_message = str(e)
            task.progress_message = "Failed"
            task.completed_at = time.time()
            logger.error(f"[Task {task.task_id[:8]}] Failed to load {task.model_id}: {e}")

    async def load_model(
        self,
        model_id: str,
        codec_id: str | None = None,
        backbone_device: str | None = None,
        codec_device: str | None = None,
    ) -> LoadedModel:
        """Synchronous load (blocks until done). Used by startup."""
        if model_id in self._models:
            logger.info(f"Model {model_id} already loaded")
            return self._models[model_id]

        info = get_backbone_info(model_id)
        if info is None:
            raise ValueError(f"Unknown model: {model_id}. Available: {list(BACKBONE_MODELS.keys())}")

        codec = codec_id or settings.default_codec
        bb_device = backbone_device or settings.resolved_backbone_device
        cc_device = codec_device or settings.default_codec_device

        if info.backend == BackendType.GGUF:
            bb_device = "cpu"

        logger.info(
            f"Loading model {model_id} (repo={info.repo}, codec={codec}, "
            f"backbone_device={bb_device}, codec_device={cc_device})"
        )

        loop = asyncio.get_event_loop()
        tts = await loop.run_in_executor(
            self._executor,
            self._create_tts_instance,
            info.repo,
            codec,
            bb_device,
            cc_device,
        )

        loaded = LoadedModel(
            model_id=model_id,
            codec_id=codec,
            tts_instance=tts,
            backbone_device=bb_device,
            codec_device=cc_device,
        )
        self._models[model_id] = loaded
        logger.info(f"Model {model_id} loaded successfully")
        return loaded

    @staticmethod
    def _create_tts_instance(
        backbone_repo: str,
        codec_repo: str,
        backbone_device: str,
        codec_device: str,
    ) -> object:
        from neutts import NeuTTS

        return NeuTTS(
            backbone_repo=backbone_repo,
            backbone_device=backbone_device,
            codec_repo=codec_repo,
            codec_device=codec_device,
        )

    async def unload_model(self, model_id: str) -> None:
        if model_id not in self._models:
            raise ValueError(f"Model {model_id} is not loaded")

        loaded = self._models.pop(model_id)
        async with loaded.lock:
            del loaded.tts_instance
        logger.info(f"Model {model_id} unloaded")

    async def switch_device(
        self,
        model_id: str,
        backbone_device: str | None = None,
        codec_device: str | None = None,
    ) -> ModelLoadingTask:
        """Unload model and reload on a different device."""
        if model_id not in self._models:
            raise ValueError(f"Model {model_id} is not loaded")

        loaded = self._models[model_id]
        info = get_backbone_info(model_id)

        if info and info.backend == BackendType.GGUF:
            raise ValueError(
                f"Model {model_id} is GGUF (llama.cpp) and only supports CPU. "
                "Device switching is not available for GGUF models."
            )

        codec_id = loaded.codec_id
        bb_device = backbone_device or loaded.backbone_device
        cc_device = codec_device or loaded.codec_device

        logger.info(f"Switching {model_id} device to backbone={bb_device}, codec={cc_device}")
        await self.unload_model(model_id)

        return await self.load_model_async(
            model_id=model_id,
            codec_id=codec_id,
            backbone_device=bb_device,
            codec_device=cc_device,
        )

    def cleanup_old_tasks(self, max_age_seconds: float = 3600) -> int:
        """Remove completed/errored tasks older than max_age_seconds."""
        now = time.time()
        to_remove = [
            tid
            for tid, t in self._loading_tasks.items()
            if t.status in (ModelLoadStatus.READY, ModelLoadStatus.ERROR)
            and t.completed_at > 0
            and (now - t.completed_at) > max_age_seconds
        ]
        for tid in to_remove:
            del self._loading_tasks[tid]
        return len(to_remove)

    async def infer(
        self,
        model_id: str,
        text: str,
        ref_codes: object,
        ref_text: str,
    ) -> np.ndarray:
        loaded = self._get_loaded(model_id)

        async with loaded.lock:
            loop = asyncio.get_event_loop()
            wav = await loop.run_in_executor(
                self._executor,
                loaded.tts_instance.infer,
                text,
                ref_codes,
                ref_text,
            )
        return wav

    async def infer_stream(
        self,
        model_id: str,
        text: str,
        ref_codes: object,
        ref_text: str,
    ) -> AsyncGenerator[np.ndarray, None]:
        loaded = self._get_loaded(model_id)
        info = get_backbone_info(model_id)

        if info is None or not info.supports_streaming:
            raise ValueError(
                f"Model {model_id} does not support streaming. "
                "Only GGUF models support infer_stream()."
            )

        queue: asyncio.Queue[np.ndarray | None] = asyncio.Queue()

        def _stream_worker() -> None:
            try:
                for chunk in loaded.tts_instance.infer_stream(text, ref_codes, ref_text):
                    queue.put_nowait(chunk)
            except Exception as e:
                logger.error(f"Streaming error for {model_id}: {e}")
            finally:
                queue.put_nowait(None)

        async with loaded.lock:
            loop = asyncio.get_event_loop()
            loop.run_in_executor(self._executor, _stream_worker)

            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                yield chunk

    async def encode_reference(self, model_id: str, audio_path: str) -> object:
        loaded = self._get_loaded(model_id)

        async with loaded.lock:
            loop = asyncio.get_event_loop()
            ref_codes = await loop.run_in_executor(
                self._executor,
                loaded.tts_instance.encode_reference,
                audio_path,
            )
        return ref_codes

    def _get_loaded(self, model_id: str) -> LoadedModel:
        loaded = self._models.get(model_id)
        if loaded is None:
            raise ValueError(
                f"Model {model_id} is not loaded. "
                f"Loaded models: {list(self._models.keys())}"
            )
        return loaded

    async def startup(self) -> None:
        for model_id in settings.default_models_list:
            try:
                await self.load_model(model_id)
            except Exception as e:
                logger.error(f"Failed to load default model {model_id}: {e}")

    async def shutdown(self) -> None:
        model_ids = list(self._models.keys())
        for model_id in model_ids:
            try:
                await self.unload_model(model_id)
            except Exception:
                pass
        self._executor.shutdown(wait=False)
