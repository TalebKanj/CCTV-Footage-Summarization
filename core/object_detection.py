from __future__ import annotations

import glob
import os
from typing import Callable, Optional

import cv2

from .config import load_config
from .gpu_memory import clear_gpu_cache
from .utils.model_download import ensure_yolo_model


def get_sorted_frame_paths(frames_dir: str, extension: str = "jpg") -> list[str]:
    frame_paths = sorted(glob.glob(os.path.join(frames_dir, f"*.{extension}")))
    if not frame_paths:
        raise ValueError(f"No frames found in directory: {frames_dir}")
    return frame_paths


def _get_torch():
    import torch  # type: ignore

    return torch


def _configure_torch_safe_globals_for_ultralytics(weights_path: Optional[str] = None) -> None:
    """PyTorch 2.6+ defaults to weights_only=True; allowlist Ultralytics model classes for safe loading.

    This avoids `_pickle.UnpicklingError: Weights only load failed` when loading official Ultralytics weights.
    """
    try:
        torch = _get_torch()
    except Exception:
        return

    try:
        import torch.serialization as serialization  # type: ignore
    except Exception:
        serialization = getattr(torch, "serialization", None)
        if serialization is None:
            return

    add_safe = getattr(serialization, "add_safe_globals", None)
    get_unsafe = getattr(serialization, "get_unsafe_globals_in_checkpoint", None)
    if add_safe is None:
        return

    # Common torch.nn containers referenced by Ultralytics checkpoints.
    try:
        from torch.nn.modules.container import (  # type: ignore
            ModuleDict,
            ModuleList,
            Sequential,
        )
    except Exception:
        ModuleDict = None  # type: ignore[assignment]
        ModuleList = None  # type: ignore[assignment]
        Sequential = None  # type: ignore[assignment]

    # Common torch.nn layers/ops referenced by YOLO models.
    try:
        from torch.nn import (  # type: ignore
            BatchNorm2d,
            Conv2d,
            Dropout,
            Identity,
            MaxPool2d,
            ReLU,
            SiLU,
            Upsample,
        )
    except Exception:
        BatchNorm2d = Conv2d = Dropout = Identity = MaxPool2d = ReLU = SiLU = Upsample = None  # type: ignore[assignment]

    try:
        from ultralytics.nn.tasks import (  # type: ignore
            ClassificationModel,
            DetectionModel,
            PoseModel,
            SegmentationModel,
        )
    except Exception:
        # Ultralytics not installed or module changed.
        return

    try:
        allow = [
            DetectionModel,
            SegmentationModel,
            PoseModel,
            ClassificationModel,
            Sequential,
            ModuleList,
            ModuleDict,
            Conv2d,
            BatchNorm2d,
            SiLU,
            ReLU,
            MaxPool2d,
            Upsample,
            Identity,
            Dropout,
        ]
        add_safe([x for x in allow if x is not None])
    except Exception:
        pass

    # Dynamically allowlist any additional globals referenced by the checkpoint file.
    if weights_path and callable(get_unsafe):
        try:
            import importlib

            unsafe = get_unsafe(weights_path) or []
            resolved = []
            for name in unsafe:
                if not isinstance(name, str) or "." not in name:
                    continue
                module_name, attr = name.rsplit(".", 1)
                try:
                    mod = importlib.import_module(module_name)
                    obj = getattr(mod, attr, None)
                    if obj is not None:
                        resolved.append(obj)
                except Exception:
                    continue
            if resolved:
                add_safe(resolved)
        except Exception:
            pass


def _select_device() -> str:
    torch = _get_torch()
    return "cuda" if torch.cuda.is_available() else "cpu"

def _device_for_ultralytics(device: Optional[str]) -> object:
    """Ultralytics expects device as 'cpu' or an int GPU id like 0."""
    if not device:
        return "cpu"
    d = str(device).strip().lower()
    if d in {"cuda", "0", "cuda:0"}:
        return 0
    if d.startswith("cuda:"):
        try:
            return int(d.split(":", 1)[1])
        except Exception:
            return 0
    return d

def _get_yolo_class():
    from ultralytics import YOLO  # Lazy import

    return YOLO


def load_yolo_model(
    progress_callback: Callable[[str, int], None] | None = None,
    model_path: str | None = None,
    model_repo: str | None = None,
    model_filename: str | None = None,
    hf_token: str | None = None,
    device: str | None = None,
):
    cfg = load_config()
    if model_path is None:
        model_path = cfg.yolo_model_path
    if model_repo is None:
        model_repo = getattr(cfg, "yolo_model_repo", "Ultralytics/yolov8n")
    if model_filename is None:
        model_filename = getattr(cfg, "yolo_model_filename", "yolov8n.pt")
    if hf_token is None:
        hf_token = getattr(cfg, "hf_token", None)

    model_path = ensure_yolo_model(
        progress_callback=progress_callback,
        model_path=model_path,
        model_repo=model_repo,
        model_filename=model_filename,
        hf_token=hf_token,
    )

    clear_gpu_cache()
    if device is None:
        device = _select_device()

    yolo = _get_yolo_class()
    _configure_torch_safe_globals_for_ultralytics(model_path)

    # Workaround for PyTorch 2.6+ where weights_only=True is the default.
    torch = _get_torch()
    original_load = torch.load
    def _patched_load(*args, **kwargs):
        if "weights_only" not in kwargs:
            kwargs["weights_only"] = False
        return original_load(*args, **kwargs)
    
    torch.load = _patched_load
    try:
        model = yolo(model_path)
    finally:
        torch.load = original_load

    # Store preferred device for inference calls.
    try:
        model._cctv_device = _device_for_ultralytics(device)  # type: ignore[attr-defined]
    except Exception:
        pass
    return model


def run_object_detection_on_frames(
    frames_dir: str,
    output_dir: str,
    model,
    config: Optional[dict] = None,
    *,
    confidence: Optional[float] = None,
    allowed_classes: Optional[list[str]] = None,
) -> None:
    if config:
        confidence = float(config.get("yolo_confidence", confidence if confidence is not None else 0.3))
        allowed_classes = config.get("allowed_classes", allowed_classes)

    if confidence is None:
        confidence = 0.3

    os.makedirs(output_dir, exist_ok=True)
    frame_paths = get_sorted_frame_paths(frames_dir)

    # Ultralytics supports list inference for speed; fall back to per-frame if needed.
    device_arg = getattr(model, "_cctv_device", None)
    try:
        if hasattr(model, "predict"):
            results = model.predict(source=frame_paths, conf=confidence, device=device_arg)
        else:
            results = model(frame_paths, conf=confidence)
        for path, result in zip(frame_paths, results):
            _annotate_and_save(path, result, output_dir, allowed_classes)
    except Exception:
        for path in frame_paths:
            if hasattr(model, "predict"):
                results = model.predict(source=path, conf=confidence, device=device_arg)
            else:
                results = model(path, conf=confidence)
            _annotate_and_save(path, results[0], output_dir, allowed_classes)


def _annotate_and_save(path: str, result, output_dir: str, allowed_classes: Optional[list[str]]) -> None:
    image = cv2.imread(path)
    if image is None:
        return

    for box in result.boxes:
        cls_id = int(box.cls)
        cls_name = result.names[cls_id]
        if allowed_classes and cls_name not in allowed_classes:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf)
        label = f"{cls_name} {conf:.2f}"

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            image,
            label,
            (x1, max(y1 - 10, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    filename = os.path.basename(path)
    cv2.imwrite(os.path.join(output_dir, filename), image)


def frames_to_video(frames_dir: str, output_video_path: str, fps: int = 12, extension: str = "jpg") -> None:
    frame_paths = get_sorted_frame_paths(frames_dir, extension)
    first_frame = cv2.imread(frame_paths[0])
    if first_frame is None:
        raise ValueError(f"Unable to read frame: {frame_paths[0]}")
    height, width = first_frame.shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    for frame_path in frame_paths:
        frame = cv2.imread(frame_path)
        if frame is None:
            continue
        video_writer.write(frame)

    video_writer.release()


def run_object_detection_pipeline(
    frames_dir: str,
    detected_dir: str,
    output_video_path: str,
    model_path: str | None = None,
    confidence: float = 0.6,
    allowed_classes: Optional[list[str]] = None,
    fps: int = 12,
):
    model = load_yolo_model(model_path=model_path)
    run_object_detection_on_frames(
        frames_dir=frames_dir,
        output_dir=detected_dir,
        model=model,
        config=None,
        confidence=confidence,
        allowed_classes=allowed_classes,
    )
    frames_to_video(frames_dir=detected_dir, output_video_path=output_video_path, fps=fps)
