from __future__ import annotations

import tempfile
from pathlib import Path

from loguru import logger

_temp_dir: Path | None = None


def get_temp_dir() -> Path:
    global _temp_dir
    if _temp_dir is None:
        _temp_dir = Path(tempfile.mkdtemp(prefix="neutts_"))
        logger.info(f"Created temp directory: {_temp_dir}")
    _temp_dir.mkdir(parents=True, exist_ok=True)
    return _temp_dir


def cleanup_temp() -> None:
    global _temp_dir
    if _temp_dir is not None and _temp_dir.exists():
        import shutil

        shutil.rmtree(_temp_dir, ignore_errors=True)
        logger.info(f"Cleaned up temp directory: {_temp_dir}")
        _temp_dir = None
