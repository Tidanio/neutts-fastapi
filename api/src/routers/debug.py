from __future__ import annotations

import platform
import subprocess
import sys

import psutil
from fastapi import APIRouter

from api.src.inference.model_manager import ModelManager
from api.src.inference.voice_manager import VoiceManager
from api.src.structures.schemas import SystemDebugResponse

router = APIRouter(prefix="/debug", tags=["Debug"])


def _nvidia_smi_info() -> dict | None:
    """Run nvidia-smi and return GPU name + driver version, or None."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.strip().split("\n")[0]
            parts = [p.strip() for p in line.split(",")]
            return {"gpu_name": parts[0], "driver_version": parts[1] if len(parts) > 1 else "unknown"}
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _build_gpu_fix_instructions(
    gpu_name: str,
    driver_version: str,
    torch_ver: str | None,
    cuda_ver: str | None,
) -> str:
    """Build OS-specific GPU fix instructions."""
    os_name = platform.system()  # "Windows", "Linux", "Darwin"
    is_docker = _is_running_in_docker()
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"

    # Detect GPU generation from name
    is_blackwell = any(x in gpu_name.upper() for x in ("RTX 50", "RTX50", "BLACKWELL", "GB2"))
    is_ada = any(x in gpu_name.upper() for x in ("RTX 40", "RTX40", "ADA"))
    needs_cu128 = is_blackwell
    min_torch = "2.6.0" if is_blackwell else "2.1.0"
    cu_tag = "cu128" if needs_cu128 else "cu124"

    # Diagnosis
    lines = [
        f"GPU '{gpu_name}' detected (driver {driver_version}) but PyTorch cannot use it.",
        f"Installed: torch=={torch_ver or 'not installed'}, CUDA=={cuda_ver or 'none'}.",
    ]

    if torch_ver is None:
        lines.append("PyTorch is not installed at all.")
    elif cuda_ver is None:
        lines.append("PyTorch is installed but was built without CUDA (CPU-only build).")
    elif is_blackwell and cuda_ver and cuda_ver < "12.8":
        lines.append(f"RTX 50xx (Blackwell) requires CUDA >= 12.8, but torch has CUDA {cuda_ver}.")
    else:
        lines.append("PyTorch CUDA version may not match your GPU architecture.")

    lines.append("")

    # OS-specific fix
    if is_docker:
        lines.append("Fix (Docker): Rebuild with the updated Dockerfile (CUDA 12.8.0 base image):")
        lines.append("  docker build -f docker/gpu/Dockerfile -t neutts-gpu .")
    elif os_name == "Windows":
        lines.append(f"Fix (Windows, Python {python_ver}):")
        lines.append(f"  pip install torch>={min_torch} --index-url https://download.pytorch.org/whl/{cu_tag}")
        lines.append("")
        lines.append("Make sure you have the latest NVIDIA driver installed:")
        lines.append("  https://www.nvidia.com/Download/index.aspx")
        if is_blackwell:
            lines.append("  RTX 50xx requires driver >= 572.16")
    elif os_name == "Linux":
        lines.append(f"Fix (Linux, Python {python_ver}):")
        lines.append(f"  pip install torch>={min_torch} --index-url https://download.pytorch.org/whl/{cu_tag}")
        lines.append("")
        lines.append("Or with conda:")
        lines.append(f"  conda install pytorch>={min_torch} pytorch-cuda=12.8 -c pytorch -c nvidia")
        lines.append("")
        lines.append("Verify NVIDIA driver: nvidia-smi")
        if is_blackwell:
            lines.append("  RTX 50xx requires driver >= 572.16")
    else:
        lines.append(f"Fix: pip install torch>={min_torch} --index-url https://download.pytorch.org/whl/{cu_tag}")

    lines.append("")
    lines.append("After installing, restart NeuTTS-FastAPI.")

    return "\n".join(lines)


def _is_running_in_docker() -> bool:
    """Check if we're running inside a Docker container."""
    try:
        with open("/proc/1/cgroup", "r") as f:
            return "docker" in f.read()
    except (FileNotFoundError, PermissionError):
        pass
    try:
        from pathlib import Path
        return Path("/.dockerenv").exists()
    except Exception:
        pass
    return False


@router.get("/system", response_model=SystemDebugResponse)
async def system_info() -> SystemDebugResponse:
    """Return system resource usage and loaded model info."""
    model_manager = ModelManager.get_instance()
    voice_manager = VoiceManager.get_instance()

    mem = psutil.virtual_memory()

    gpu_available = False
    gpu_info = None
    torch_version = None
    cuda_version = None
    cuda_driver_version = None
    gpu_detected_but_unusable = False
    gpu_fix_instructions = None

    try:
        import torch

        torch_version = torch.__version__
        cuda_version = torch.version.cuda

        if torch.cuda.is_available():
            gpu_available = True
            gpu_info = []
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                allocated = torch.cuda.memory_allocated(i) / (1024**3)
                total = props.total_mem / (1024**3)
                gpu_info.append({
                    "index": i,
                    "name": props.name,
                    "total_gb": round(total, 2),
                    "allocated_gb": round(allocated, 2),
                })
    except ImportError:
        pass

    # Check nvidia-smi for GPU detection even if torch can't use it
    smi = _nvidia_smi_info()
    if smi:
        cuda_driver_version = smi["driver_version"]
        if not gpu_available:
            gpu_detected_but_unusable = True
            gpu_fix_instructions = _build_gpu_fix_instructions(
                smi["gpu_name"], smi["driver_version"], torch_version, cuda_version,
            )

    return SystemDebugResponse(
        cpu_count=psutil.cpu_count() or 0,
        cpu_percent=psutil.cpu_percent(),
        memory_total_gb=round(mem.total / (1024**3), 2),
        memory_used_gb=round(mem.used / (1024**3), 2),
        memory_percent=mem.percent,
        gpu_available=gpu_available,
        gpu_info=gpu_info,
        torch_version=torch_version,
        cuda_version=cuda_version,
        cuda_driver_version=cuda_driver_version,
        gpu_detected_but_unusable=gpu_detected_but_unusable,
        gpu_fix_instructions=gpu_fix_instructions,
        models_loaded=list(model_manager.loaded_models.keys()),
        voices_available=len(voice_manager.voices),
    )
