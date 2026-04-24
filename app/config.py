import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class AppConfig:
    """Central application configuration for CCTV Footage Summarization."""

    video_path: str = "data/inputs/test.mp4"
    yolo_model_path: str = "models/yolov8n.pt"

    pixel_diff_thresh: int = 15
    percent_changed_thresh: float = 1.5

    summary_fps: int = 12
    yolo_confidence: float = 0.3
    allowed_classes: List[str] = field(default_factory=lambda: ["person", "car"])

    merge_gap_sec: float = 1.0
    pre_event_sec: float = 1.0
    post_event_sec: float = 2.0

    mog2_history: int = 500
    mog2_var_threshold: int = 15
    mog2_detect_shadows: bool = False

    buffer_duration_sec: float = 1.5

    cuda_alloc_conf: str = "expandable_segments:True,max_split_size_mb:512"
    max_memory_fraction: float = 0.85

    output_base: str = "results"
    cache_db_path: str = "data/summary_cache.json"

    def __post_init__(self):
        os.makedirs(os.path.dirname(self.cache_db_path) if os.path.dirname(self.cache_db_path) else "data", exist_ok=True)


def load_config() -> AppConfig:
    """Load configuration from environment variables with defaults."""
    return AppConfig(
        video_path=os.getenv("VIDEO_PATH", "data/inputs/test.mp4"),
        yolo_model_path=os.getenv("YOLO_MODEL_PATH", "models/yolov8n.pt"),
        pixel_diff_thresh=int(os.getenv("PIXEL_DIFF_THRESH", "15")),
        percent_changed_thresh=float(os.getenv("PERCENT_CHANGED_THRESH", "0.15")),
        summary_fps=int(os.getenv("SUMMARY_FPS", "12")),
        yolo_confidence=float(os.getenv("YOLO_CONFIDENCE", "0.3")),
        allowed_classes=os.getenv("ALLOWED_CLASSES", "person,car").split(","),
        merge_gap_sec=float(os.getenv("MERGE_GAP_SEC", "2.0")),
        pre_event_sec=float(os.getenv("PRE_EVENT_SEC", "2.0")),
        post_event_sec=float(os.getenv("POST_EVENT_SEC", "4.0")),
        output_base=os.getenv("OUTPUT_BASE", "results"),
        cuda_alloc_conf=os.getenv("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:512"),
        max_memory_fraction=float(os.getenv("MAX_MEMORY_FRACTION", "0.85")),
    )


config = load_config()