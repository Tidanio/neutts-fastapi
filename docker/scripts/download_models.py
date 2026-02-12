"""Pre-download models during Docker build or startup."""
from __future__ import annotations

import os
import sys


def main() -> None:
    models_str = os.environ.get("NEUTTS_DEFAULT_MODELS", "neutts-nano-q4-gguf")
    codec = os.environ.get("NEUTTS_DEFAULT_CODEC", "neuphonic/neucodec-onnx-decoder")

    models = [m.strip() for m in models_str.split(",") if m.strip()]

    # Import model config to resolve repos
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from api.src.core.model_config import get_backbone_info

    print(f"Pre-downloading {len(models)} model(s) and codec '{codec}'...")

    for model_id in models:
        info = get_backbone_info(model_id)
        if info is None:
            print(f"  WARNING: Unknown model '{model_id}', skipping")
            continue

        print(f"  Downloading backbone: {info.repo}")
        try:
            from huggingface_hub import snapshot_download

            snapshot_download(info.repo)
            print(f"  OK: {info.repo}")
        except Exception as e:
            print(f"  FAILED: {info.repo} - {e}")

    print(f"  Downloading codec: {codec}")
    try:
        from huggingface_hub import snapshot_download

        snapshot_download(codec)
        print(f"  OK: {codec}")
    except Exception as e:
        print(f"  FAILED: {codec} - {e}")

    print("Download complete.")


if __name__ == "__main__":
    main()
