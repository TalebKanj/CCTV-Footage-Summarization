import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class AppConfig:
    """Central configuration for CCTV Footage Summarization."""

    video_path: str = "data/inputs/test.mp4"

    pixel_diff_thresh: int = 15
    percent_changed_thresh: float = 0.15

    summary_fps: int = 12
    yolo_confidence: float = 0.3
    allowed_classes: List[str] = field(default_factory=lambda: ["person", "car"])

    merge_gap_sec: float = 2.0
    pre_event_sec: float = 2.0
    post_event_sec: float = 4.0

    output_base: str = "results"
    cache_db_path: str = "data/summary_cache.json"
    history_db_path: str = "data/history.json"
    settings_db_path: str = "data/settings.json"
    runtime_logs_path: str = "data/runtime_logs.json"
    input_dir: str = "data/inputs"

    cuda_alloc_conf: str = "expandable_segments:True,max_split_size_mb:512"
    max_memory_fraction: float = 0.85

    def __post_init__(self):
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.cache_db_path) or "data", exist_ok=True)
        os.makedirs(self.output_base, exist_ok=True)


def load_config() -> AppConfig:
    """Load configuration from environment variables with safe defaults."""
    return AppConfig(
        video_path=os.getenv("VIDEO_PATH", "data/inputs/test.mp4"),
        pixel_diff_thresh=int(os.getenv("PIXEL_DIFF_THRESH", "15")),
        percent_changed_thresh=float(os.getenv("PERCENT_CHANGED_THRESH", "0.15")),
        summary_fps=int(os.getenv("SUMMARY_FPS", "12")),
        yolo_confidence=float(os.getenv("YOLO_CONFIDENCE", "0.3")),
        allowed_classes=os.getenv("ALLOWED_CLASSES", "person,car").split(","),
        merge_gap_sec=float(os.getenv("MERGE_GAP_SEC", "2.0")),
        pre_event_sec=float(os.getenv("PRE_EVENT_SEC", "2.0")),
        post_event_sec=float(os.getenv("POST_EVENT_SEC", "4.0")),
        output_base=os.getenv("OUTPUT_BASE", "results"),
        cache_db_path=os.getenv("CACHE_DB_PATH", "data/summary_cache.json"),
        input_dir=os.getenv("INPUT_DIR", "data/inputs"),
        cuda_alloc_conf=os.getenv("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:512"),
        max_memory_fraction=float(os.getenv("MAX_MEMORY_FRACTION", "0.85")),
    )


config = load_config()
