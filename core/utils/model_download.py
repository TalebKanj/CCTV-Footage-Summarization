from __future__ import annotations

import os
from typing import Callable, Optional

from huggingface_hub import hf_hub_download, try_to_load_from_cache
from huggingface_hub.utils import HfHubHTTPError
from huggingface_hub.errors import RepositoryNotFoundError, EntryNotFoundError, GatedRepoError, RevisionNotFoundError

from ..config import load_config


# NOTE: Ultralytics does not provide `Ultralytics/yolov8n` weights on HuggingFace.
# Use the official YOLOv8 repo instead.
DEFAULT_MODEL_REPO = "Ultralytics/YOLOv8"
DEFAULT_MODEL_FILE = "yolov8x.pt"


def ensure_yolo_model(
    progress_callback: Callable[[str, int], None] | None = None,
    *,
    model_path: str | None = None,
    model_repo: str = DEFAULT_MODEL_REPO,
    model_filename: str = DEFAULT_MODEL_FILE,
    force_download: bool = False,
    hf_token: str | None = None,
) -> str:
    """Ensure a YOLO weights file exists locally and return its path.

    Backward compatible:
    - existing callers pass only `progress_callback`
    Enhanced:
    - can provide explicit `model_path`/repo/filename and uses HF cache when possible.
    """
    config = load_config()

    if model_path is None:
        model_path = config.yolo_model_path
    if not model_repo:
        model_repo = config.yolo_model_repo
    if not model_filename:
        model_filename = config.yolo_model_filename
    if hf_token is None:
        hf_token = getattr(config, "hf_token", None)

    if progress_callback:
        progress_callback("جاري تحميل النموذج...", 0)

    if model_path and os.path.exists(model_path) and not force_download:
        if progress_callback:
            progress_callback("تم العثور على النموذج محلياً", 100)
        return model_path

    # Preferred: use Ultralytics official asset downloader (works for yolov8*.pt and avoids HF repo mismatches).
    try:
        from ultralytics.utils.downloads import attempt_download_asset  # type: ignore

        if model_filename and model_filename.lower().endswith(".pt") and model_filename.lower().startswith("yolov8"):
            if progress_callback:
                progress_callback("جاري تنزيل النموذج عبر Ultralytics...", 15)
            downloaded_asset = attempt_download_asset(model_filename)
            if downloaded_asset and os.path.exists(downloaded_asset):
                if progress_callback:
                    progress_callback("تم تنزيل النموذج بنجاح", 100)
                return downloaded_asset
    except Exception:
        # Fall back to HF logic below.
        pass

    cached_path = try_to_load_from_cache(repo_id=model_repo, filename=model_filename)
    if cached_path and not force_download:
        if progress_callback:
            progress_callback("تم تحميل النموذج من الذاكرة المؤقتة", 100)
        return cached_path

    if progress_callback:
        progress_callback("جاري تنزيل النموذج من HuggingFace...", 10)

    try:
        downloaded_path = hf_hub_download(
            repo_id=model_repo,
            filename=model_filename,
            force_download=force_download,
            token=hf_token,
        )
    except (RepositoryNotFoundError, RevisionNotFoundError) as exc:
        raise RuntimeError(
            "فشل تنزيل نموذج YOLO من HuggingFace: المستودع غير موجود. "
            "تحقق من (repo_id) أو قم بتنزيل الملف يدوياً ووضعه في: "
            f"{model_path}"
        ) from None
    except (EntryNotFoundError,) as exc:
        raise RuntimeError(
            "فشل تنزيل نموذج YOLO من HuggingFace: ملف الأوزان غير موجود داخل المستودع. "
            "تحقق من اسم الملف أو قم بتنزيله يدوياً ووضعه في: "
            f"{model_path}"
        ) from None
    except (GatedRepoError,) as exc:
        raise RuntimeError(
            "فشل تنزيل نموذج YOLO من HuggingFace: المستودع مقيد/خاص. "
            "أضف HuggingFace Token صالحاً في الإعدادات ثم أعد المحاولة."
        ) from None
    except HfHubHTTPError as exc:
        raise RuntimeError(
            "فشل تنزيل نموذج YOLO من HuggingFace بسبب خطأ في الاتصال/الاستجابة. "
            "تحقق من الاتصال، (repo_id/filename)، أو قم بتنزيل الملف يدوياً ووضعه في: "
            f"{model_path}"
        ) from None
    except Exception as exc:
        raise RuntimeError(
            "فشل تنزيل نموذج YOLO من HuggingFace. "
            "تحقق من (repo_id/filename) أو قم بتنزيل الملف يدوياً ووضعه في: "
            f"{model_path}"
        ) from None

    if progress_callback:
        progress_callback("تم تنزيل النموذج بنجاح", 100)

    return downloaded_path


def get_cached_model_path(model_repo: str = DEFAULT_MODEL_REPO, model_filename: str = DEFAULT_MODEL_FILE) -> Optional[str]:
    return try_to_load_from_cache(repo_id=model_repo, filename=model_filename)
