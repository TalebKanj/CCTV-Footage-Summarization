import os
import torch


def init_gpu_memory(alloc_conf: str = "expandable_segments:True,max_split_size_mb:512", max_fraction: float = 0.85) -> bool:
    """Initialize PyTorch CUDA memory settings for maximum VRAM utilization.

    Args:
        alloc_conf: PYTORCH_CUDA_ALLOC_CONF string.
        max_fraction: Max memory fraction (0.0-1.0).

    Returns:
        True if CUDA available and initialized, False otherwise.
    """
    if not torch.cuda.is_available():
        return False

    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = alloc_conf
    torch.cuda.set_per_process_memory_fraction(max_fraction)
    return True


def get_gpu_memory_info() -> dict | None:
    """Get current GPU memory usage information.

    Returns:
        Dict with allocated_mb, reserved_mb, free_mb, total_mb or None if no GPU.
    """
    if not torch.cuda.is_available():
        return None

    props = torch.cuda.get_device_properties(0)
    total_bytes = props.total_memory
    allocated_bytes = torch.cuda.memory_allocated()
    reserved_bytes = torch.cuda.memory_reserved()

    return {
        "allocated_mb": allocated_bytes / (1024 ** 2),
        "reserved_mb": reserved_bytes / (1024 ** 2),
        "free_mb": (total_bytes - allocated_bytes) / (1024 ** 2),
        "total_mb": total_bytes / (1024 ** 2),
    }


def clear_gpu_cache() -> bool:
    """Clear CUDA cache to free unused memory.

    Returns:
        True if CUDA available, False otherwise.
    """
    if not torch.cuda.is_available():
        return False

    torch.cuda.empty_cache()
    return True