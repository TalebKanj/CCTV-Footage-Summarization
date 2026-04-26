from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional


def _default_runtime_base_dir() -> str:
    """Return a writable base directory for runtime data when packaged as an EXE."""
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "CCTVAnalyzer")


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


@dataclass
class AppConfig:
    """Central configuration for CCTV Footage Summarization."""

    video_path: str = "data/inputs/test.mp4"

    # Motion defaults tuned to ignore slight changes (leaves, weak wind, small lighting jitter).
    # `percent_changed_thresh` is in percent (0..100), not a 0..1 fraction.
    pixel_diff_thresh: int = 28
    percent_changed_thresh: float = 1.2
    frame_skip: int = 3
    resize_width: int = 640
    morph_kernel: int = 5
    morph_open_iters: int = 2
    morph_dilate_iters: int = 2

    summary_fps: int = 12
    merge_gap_sec: float = 2.0
    pre_event_sec: float = 2.0
    post_event_sec: float = 4.0

    yolo_confidence: float = 0.3
    yolo_model_repo: str = "Ultralytics/YOLOv8"
    yolo_model_filename: str = "yolov8x.pt"
    yolo_model_path: str = "models/yolov8x.pt"
    hf_token: Optional[str] = None
    allowed_classes: List[str] = field(default_factory=lambda: ["person", "car"])
    enable_object_detection: bool = False

    output_base: str = "results"
    cache_db_path: str = "data/summary_cache.json"
    history_db_path: str = "data/history.json"
    settings_db_path: str = "data/settings.json"
    runtime_logs_path: str = "data/runtime_logs.json"
    input_dir: str = "data/inputs"

    cuda_alloc_conf: str = "expandable_segments:True,max_split_size_mb:512"
    max_memory_fraction: float = 0.85

    mog2_history: int = 500
    mog2_var_threshold: int = 15
    buffer_duration_sec: float = 1.5

    def __post_init__(self) -> None:
        os.makedirs(self.input_dir, exist_ok=True)

        model_dir = os.path.dirname(self.yolo_model_path)
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)

        os.makedirs(os.path.dirname(self.cache_db_path) or "data", exist_ok=True)
        os.makedirs(self.output_base, exist_ok=True)


def load_config() -> AppConfig:
    """Load configuration from environment variables with safe defaults."""
    if _is_frozen():
        base_dir = _default_runtime_base_dir()
        default_input_dir = os.path.join(base_dir, "inputs")
        default_video_path = os.path.join(default_input_dir, "test.mp4")
        default_output_base = os.path.join(base_dir, "results")
        default_data_dir = os.path.join(base_dir, "data")
        default_models_dir = os.path.join(base_dir, "models")
        default_cache_db_path = os.path.join(default_data_dir, "summary_cache.json")
        default_history_db_path = os.path.join(default_data_dir, "history.json")
        default_settings_db_path = os.path.join(default_data_dir, "settings.json")
        default_runtime_logs_path = os.path.join(default_data_dir, "runtime_logs.json")
        default_yolo_model_path = os.path.join(default_models_dir, "yolov8x.pt")
    else:
        default_input_dir = "data/inputs"
        default_video_path = "data/inputs/test.mp4"
        default_output_base = "results"
        default_cache_db_path = "data/summary_cache.json"
        default_history_db_path = "data/history.json"
        default_settings_db_path = "data/settings.json"
        default_runtime_logs_path = "data/runtime_logs.json"
        default_yolo_model_path = "models/yolov8x.pt"

    return AppConfig(
        video_path=os.getenv("VIDEO_PATH", default_video_path),
        pixel_diff_thresh=int(os.getenv("PIXEL_DIFF_THRESH", "15")),
        percent_changed_thresh=float(os.getenv("PERCENT_CHANGED_THRESH", "0.15")),
        frame_skip=int(os.getenv("FRAME_SKIP", "3")),
        resize_width=int(os.getenv("RESIZE_WIDTH", "640")),
        morph_kernel=int(os.getenv("MORPH_KERNEL", "3")),
        morph_open_iters=int(os.getenv("MORPH_OPEN_ITERS", "1")),
        morph_dilate_iters=int(os.getenv("MORPH_DILATE_ITERS", "1")),
        summary_fps=int(os.getenv("SUMMARY_FPS", "12")),
        merge_gap_sec=float(os.getenv("MERGE_GAP_SEC", "2.0")),
        pre_event_sec=float(os.getenv("PRE_EVENT_SEC", "2.0")),
        post_event_sec=float(os.getenv("POST_EVENT_SEC", "4.0")),
        yolo_confidence=float(os.getenv("YOLO_CONFIDENCE", "0.3")),
        yolo_model_repo=os.getenv("YOLO_MODEL_REPO", "Ultralytics/YOLOv8"),
        yolo_model_filename=os.getenv("YOLO_MODEL_FILENAME", "yolov8x.pt"),
        yolo_model_path=os.getenv("YOLO_MODEL_PATH", default_yolo_model_path),
        hf_token=os.getenv("HF_TOKEN", None) or None,
        allowed_classes=[c.strip() for c in os.getenv("ALLOWED_CLASSES", "person,car").split(",") if c.strip()],
        enable_object_detection=os.getenv("ENABLE_OBJECT_DETECTION", "0").strip() in {"1", "true", "True", "YES", "yes"},
        output_base=os.getenv("OUTPUT_BASE", default_output_base),
        cache_db_path=os.getenv("CACHE_DB_PATH", default_cache_db_path),
        history_db_path=os.getenv("HISTORY_DB_PATH", default_history_db_path),
        settings_db_path=os.getenv("SETTINGS_DB_PATH", default_settings_db_path),
        runtime_logs_path=os.getenv("RUNTIME_LOGS_PATH", default_runtime_logs_path),
        input_dir=os.getenv("INPUT_DIR", default_input_dir),
        cuda_alloc_conf=os.getenv(
            "PYTORCH_CUDA_ALLOC_CONF",
            "expandable_segments:True,max_split_size_mb:512",
        ),
        max_memory_fraction=float(os.getenv("MAX_MEMORY_FRACTION", "0.85")),
        mog2_history=int(os.getenv("MOG2_HISTORY", "500")),
        mog2_var_threshold=int(os.getenv("MOG2_VAR_THRESHOLD", "15")),
        buffer_duration_sec=float(os.getenv("BUFFER_DURATION_SEC", "1.5")),
    )


def config_from_overrides(overrides: Optional[Dict[str, Any]], base: Optional[AppConfig] = None) -> AppConfig:
    """Create an AppConfig from a base config and a dict of overrides."""
    cfg = base or load_config()
    if not overrides:
        return cfg

    allowed_classes = overrides.get("allowed_classes")
    if allowed_classes is not None:
        if isinstance(allowed_classes, str):
            overrides = {**overrides, "allowed_classes": [c.strip() for c in allowed_classes.split(",") if c.strip()]}
        elif isinstance(allowed_classes, (set, tuple)):
            overrides = {**overrides, "allowed_classes": list(allowed_classes)}

    filtered: Dict[str, Any] = {}
    for key, value in overrides.items():
        if hasattr(cfg, key):
            filtered[key] = value

    return replace(cfg, **filtered)


# Backward-compatible module-level values (used by older code and `api.py`).
config = load_config()

pixel_diff_thresh = config.pixel_diff_thresh
percent_changed_thresh = config.percent_changed_thresh
summary_fps = config.summary_fps
merge_gap_sec = config.merge_gap_sec
pre_event_sec = config.pre_event_sec
post_event_sec = config.post_event_sec

yolo_confidence = config.yolo_confidence
allowed_classes = config.allowed_classes
yolo_model_repo = config.yolo_model_repo
yolo_model_filename = config.yolo_model_filename
yolo_model_path = config.yolo_model_path
hf_token = config.hf_token

mog2_history = config.mog2_history
mog2_var_threshold = config.mog2_var_threshold
buffer_duration_sec = config.buffer_duration_sec

cuda_alloc_conf = config.cuda_alloc_conf
max_memory_fraction = config.max_memory_fraction

frame_skip = config.frame_skip
resize_width = config.resize_width
morph_kernel = config.morph_kernel
morph_open_iters = config.morph_open_iters
morph_dilate_iters = config.morph_dilate_iters
enable_object_detection = config.enable_object_detection
