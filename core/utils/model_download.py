import os
from typing import Callable, Optional
from huggingface_hub import hf_hub_download, try_to_load_from_cache


DEFAULT_MODEL_REPO = "Ultralytics/yolov8n"
DEFAULT_MODEL_FILE = "yolov8n.pt"


def ensure_yolo_model(
    model_path: str | None = None,
    model_repo: str = DEFAULT_MODEL_REPO,
    progress_callback: Callable[[str, int], None] | None = None,
    force_download: bool = False,
) -> str:
    if progress_callback:
        progress_callback("جاري تحميل النموذج...", 0)
    
    if model_path and os.path.exists(model_path) and not force_download:
        return model_path
    
    cached_path = try_to_load_from_cache(
        repo_id=model_repo,
        filename=DEFAULT_MODEL_FILE,
    )
    if cached_path and not force_download:
        if progress_callback:
            progress_callback("تم تحميل النموذج من الذاكرة المؤقتة", 100)
        return cached_path
    
    if progress_callback:
        progress_callback("جاري تنزيل النموذج من HuggingFace...", 10)
    
    downloaded_path = hf_hub_download(
        repo_id=model_repo,
        filename=DEFAULT_MODEL_FILE,
        force_download=force_download,
    )
    
    if progress_callback:
        progress_callback("تم تنزيل النموذج بنجاح", 100)
    
    return downloaded_path


def get_cached_model_path(model_repo: str = DEFAULT_MODEL_REPO) -> Optional[str]:
    return try_to_load_from_cache(
        repo_id=model_repo,
        filename=DEFAULT_MODEL_FILE,
    )