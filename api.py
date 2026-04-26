from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
import shutil
from typing import Any, Callable, Dict, List, Optional, Tuple


ProgressCallback = Callable[[str, int], None]


def get_default_config() -> Dict:
    """Return a default config dict derived from `core/config.py`."""
    from core import config as core_config

    return {
        "pixel_diff_thresh": core_config.pixel_diff_thresh,
        "percent_changed_thresh": core_config.percent_changed_thresh,
        "frame_skip": core_config.frame_skip,
        "resize_width": getattr(core_config, "resize_width", 640),
        "morph_kernel": getattr(core_config, "morph_kernel", 3),
        "morph_open_iters": getattr(core_config, "morph_open_iters", 1),
        "morph_dilate_iters": getattr(core_config, "morph_dilate_iters", 1),
        "summary_fps": core_config.summary_fps,
        "merge_gap_sec": getattr(core_config, "merge_gap_sec", 2.0),
        "pre_event_sec": getattr(core_config, "pre_event_sec", 2.0),
        "post_event_sec": getattr(core_config, "post_event_sec", 4.0),
        "yolo_confidence": core_config.yolo_confidence,
        "yolo_model_repo": getattr(core_config, "yolo_model_repo", "Ultralytics/YOLOv8"),
        "yolo_model_filename": getattr(core_config, "yolo_model_filename", "yolov8x.pt"),
        "yolo_model_path": getattr(core_config, "yolo_model_path", os.path.join("models", "yolov8x.pt")),
        "hf_token": getattr(core_config, "hf_token", None),
        "allowed_classes": list(core_config.allowed_classes),
        "enable_object_detection": getattr(core_config, "enable_object_detection", False),
    }


def normalize_config(config: Optional[Dict]) -> Dict:
    """Fill missing keys with defaults and normalize types."""
    base = get_default_config()
    if not config:
        return base

    merged = {**base, **config}

    def _as_int(value: Any, default: int) -> int:
        try:
            if value is None or value == "":
                return default
            return int(value)
        except Exception:
            return default

    def _as_float(value: Any, default: float) -> float:
        try:
            if value is None or value == "":
                return default
            return float(value)
        except Exception:
            return default

    def _as_bool(value: Any, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            v = value.strip().lower()
            if v in {"1", "true", "yes", "y", "on"}:
                return True
            if v in {"0", "false", "no", "n", "off"}:
                return False
        return default

    # Numeric settings (guard against nulls and bad types from settings.json)
    merged["pixel_diff_thresh"] = _as_int(merged.get("pixel_diff_thresh"), base["pixel_diff_thresh"])
    merged["frame_skip"] = _as_int(merged.get("frame_skip"), base["frame_skip"])
    merged["resize_width"] = _as_int(merged.get("resize_width"), base["resize_width"])
    merged["morph_kernel"] = _as_int(merged.get("morph_kernel"), base["morph_kernel"])
    merged["morph_open_iters"] = _as_int(merged.get("morph_open_iters"), base["morph_open_iters"])
    merged["morph_dilate_iters"] = _as_int(merged.get("morph_dilate_iters"), base["morph_dilate_iters"])
    merged["summary_fps"] = _as_int(merged.get("summary_fps"), base["summary_fps"])

    merged["percent_changed_thresh"] = _as_float(merged.get("percent_changed_thresh"), base["percent_changed_thresh"])
    merged["merge_gap_sec"] = _as_float(merged.get("merge_gap_sec"), base["merge_gap_sec"])
    merged["pre_event_sec"] = _as_float(merged.get("pre_event_sec"), base["pre_event_sec"])
    merged["post_event_sec"] = _as_float(merged.get("post_event_sec"), base["post_event_sec"])
    merged["yolo_confidence"] = _as_float(merged.get("yolo_confidence"), base["yolo_confidence"])

    merged["enable_object_detection"] = _as_bool(
        merged.get("enable_object_detection"),
        base.get("enable_object_detection", False),
    )

    if "yolo_model_path" in merged and merged["yolo_model_path"] is not None:
        merged["yolo_model_path"] = str(merged["yolo_model_path"])
    if "yolo_model_repo" in merged and merged["yolo_model_repo"] is not None:
        merged["yolo_model_repo"] = str(merged["yolo_model_repo"])
    if "yolo_model_filename" in merged and merged["yolo_model_filename"] is not None:
        merged["yolo_model_filename"] = str(merged["yolo_model_filename"])

    # Migrate older invalid defaults.
    if merged.get("yolo_model_repo") in {"Ultralytics/yolov8n", "Ultralytics/yolov8x", "Ultralytics/yolov8"}:
        merged["yolo_model_repo"] = "Ultralytics/YOLOv8"

    if not merged.get("yolo_model_filename"):
        # Best effort derive from path, otherwise fall back.
        try:
            base = os.path.basename(str(merged.get("yolo_model_path") or "")).strip()
        except Exception:
            base = ""
        merged["yolo_model_filename"] = base or "yolov8x.pt"

    allowed_classes = merged.get("allowed_classes")
    if allowed_classes is None:
        merged["allowed_classes"] = base["allowed_classes"]
    elif isinstance(allowed_classes, (set, tuple)):
        merged["allowed_classes"] = list(allowed_classes)
    elif isinstance(allowed_classes, str):
        parts = [p.strip() for p in allowed_classes.split(",") if p.strip()]
        merged["allowed_classes"] = parts or base["allowed_classes"]
    elif not isinstance(allowed_classes, list):
        merged["allowed_classes"] = [str(allowed_classes)]
    else:
        merged["allowed_classes"] = [str(x) for x in allowed_classes if str(x).strip()]
        if not merged["allowed_classes"]:
            merged["allowed_classes"] = base["allowed_classes"]

    if not merged.get("yolo_model_path"):
        merged["yolo_model_path"] = base.get("yolo_model_path")

    hf_token = merged.get("hf_token")
    if hf_token is None or hf_token == "":
        merged["hf_token"] = None
    else:
        merged["hf_token"] = str(hf_token).strip() or None

    return merged


def summarize_video(input_path: str, config: Optional[Dict], progress_callback: ProgressCallback) -> Dict:
    """Bridge to the core summarization pipeline.

    Rule: `core/` code must only be called from this module.
    """
    from core.summarizer import summarize_video as core_summarize_video

    safe_config = normalize_config(config)
    try:
        print(f"[DEBUG] api.summarize_video: input={input_path}")
        redacted = dict(safe_config)
        if redacted.get("hf_token"):
            redacted["hf_token"] = "***"
        print(f"[DEBUG] api.summarize_video: normalized_config={redacted}")
    except Exception:
        pass
    return core_summarize_video(input_path, safe_config, progress_callback)


def get_paths() -> Dict[str, str]:
    """Return configured data paths (cache/history/settings/logs)."""
    from core.config import load_config

    cfg = load_config()
    return {
        "cache_db_path": cfg.cache_db_path,
        "history_db_path": cfg.history_db_path,
        "settings_db_path": cfg.settings_db_path,
        "runtime_logs_path": cfg.runtime_logs_path,
        "output_base": cfg.output_base,
        "input_dir": cfg.input_dir,
    }


def load_settings() -> Dict[str, Any]:
    """Load user settings from the JSON settings DB, merged onto defaults."""
    paths = get_paths()
    defaults = get_default_config()
    path = paths["settings_db_path"]
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f) or {}
        except Exception:
            saved = {}
        if isinstance(saved, dict):
            defaults.update(saved)
    return normalize_config(defaults)


def save_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and persist settings; returns the normalized settings."""
    paths = get_paths()
    normalized = normalize_config(settings)
    os.makedirs(os.path.dirname(paths["settings_db_path"]) or ".", exist_ok=True)
    with open(paths["settings_db_path"], "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
    return normalized


def get_video_info(video_path: str) -> Dict[str, Any]:
    """Lightweight video metadata extraction (no core calls)."""
    import cv2

    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()

    duration_sec = (frame_count / fps) if fps > 0 and frame_count > 0 else None

    stat = os.stat(video_path)
    return {
        "path": os.path.abspath(video_path),
        "name": os.path.basename(video_path),
        "size_bytes": int(stat.st_size),
        "fps": fps,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "duration_sec": duration_sec,
    }


def format_file_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0 or unit == "TB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{num_bytes} B"


def compute_sha256(file_path: str, chunk_size: int = 1024 * 1024) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_history_db(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            db = json.load(f) or {}
        if isinstance(db, dict) and "videos" in db and isinstance(db["videos"], list):
            return db
    return {"videos": []}


def _load_cache_db(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                db = json.load(f) or {}
            return db if isinstance(db, dict) else {}
        except Exception:
            return {}
    return {}


def _save_cache_db(path: str, db: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def remove_cache_entry(checksum: str) -> None:
    if not checksum:
        return
    paths = get_paths()
    db = _load_cache_db(paths["cache_db_path"])
    # Cache may be stored as either:
    # - legacy key: "<checksum>"
    # - new key: "<checksum>:<config_hash>"
    to_delete = []
    for key in list(db.keys()):
        if key == checksum or key.startswith(f"{checksum}:"):
            to_delete.append(key)
            continue
        entry = db.get(key)
        if isinstance(entry, dict) and str(entry.get("input_checksum") or "") == checksum:
            to_delete.append(key)
    if not to_delete:
        return
    try:
        for key in to_delete:
            db.pop(key, None)
        _save_cache_db(paths["cache_db_path"], db)
    except Exception:
        pass


def clear_cache() -> None:
    """Clear the summarization cache DB (summary_cache.json)."""
    try:
        from core.summarizer import clear_cache as core_clear_cache

        core_clear_cache()
    except Exception:
        # Fallback: just delete the file if it exists.
        paths = get_paths()
        try:
            if os.path.exists(paths["cache_db_path"]):
                os.remove(paths["cache_db_path"])
        except Exception:
            pass


def list_history() -> List[Dict[str, Any]]:
    paths = get_paths()
    db = _load_history_db(paths["history_db_path"])
    return list(reversed(db.get("videos", [])))


def add_history_entry(input_path: str, result: Dict[str, Any], config_snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    paths = get_paths()
    db = _load_history_db(paths["history_db_path"])

    video_name = result.get("video_name") or os.path.basename(input_path)
    entry = {
        "id": str(uuid.uuid4()),
        "video_name": video_name,
        "checksum": result.get("checksum"),
        "timestamp": datetime.now().isoformat(),
        "input_path": os.path.abspath(input_path),
        "output_dir": result.get("output_dir"),
        "config_snapshot": config_snapshot or result.get("config_snapshot") or {},
        "duration_sec": result.get("duration_sec"),
        "frames_reduced_pct": result.get("frames_reduced_pct"),
        "segments_count": result.get("segments_count"),
        "cached": bool(result.get("cached")),
        "segments_video": result.get("segments_video"),
        "frames_video": result.get("frames_video"),
        "detected_video": result.get("detected_video"),
    }

    db.setdefault("videos", []).append(entry)
    os.makedirs(os.path.dirname(paths["history_db_path"]) or ".", exist_ok=True)
    with open(paths["history_db_path"], "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

    return entry


def _is_within_dir(child_path: str, parent_dir: str) -> bool:
    child = os.path.normcase(os.path.abspath(child_path))
    parent = os.path.normcase(os.path.abspath(parent_dir))
    if not parent.endswith(os.sep):
        parent = parent + os.sep
    return child.startswith(parent)


def _cleanup_empty_parents(path: str, stop_dir: str) -> None:
    """Remove empty parent directories up to (but not including) stop_dir."""
    try:
        current = os.path.abspath(path)
        stop = os.path.abspath(stop_dir)
        if not _is_within_dir(current, stop):
            return
        while True:
            parent = os.path.dirname(current)
            if os.path.normcase(current) == os.path.normcase(stop):
                break
            try:
                if os.path.isdir(current) and not os.listdir(current):
                    os.rmdir(current)
            except Exception:
                break
            if parent == current:
                break
            current = parent
    except Exception:
        pass


def delete_history_entry(entry_id: str, *, delete_results: bool = False) -> None:
    paths = get_paths()
    db = _load_history_db(paths["history_db_path"])
    remaining = []
    for entry in db.get("videos", []):
        if entry.get("id") == entry_id:
            try:
                remove_cache_entry(str(entry.get("checksum") or ""))
            except Exception:
                pass
            if delete_results:
                out_dir = entry.get("output_dir")
                if out_dir and os.path.exists(out_dir) and _is_within_dir(out_dir, paths["output_base"]):
                    try:
                        shutil.rmtree(out_dir)
                        _cleanup_empty_parents(out_dir, paths["output_base"])
                    except Exception:
                        pass
            continue
        remaining.append(entry)
    db["videos"] = remaining
    os.makedirs(os.path.dirname(paths["history_db_path"]) or ".", exist_ok=True)
    with open(paths["history_db_path"], "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def clear_history(*, delete_results: bool = False, clear_cache_db: bool = True) -> None:
    paths = get_paths()
    if delete_results:
        db = _load_history_db(paths["history_db_path"])
        for entry in db.get("videos", []):
            out_dir = entry.get("output_dir")
            if out_dir and os.path.exists(out_dir) and _is_within_dir(out_dir, paths["output_base"]):
                try:
                    shutil.rmtree(out_dir)
                    _cleanup_empty_parents(out_dir, paths["output_base"])
                except Exception:
                    pass
            try:
                remove_cache_entry(str(entry.get("checksum") or ""))
            except Exception:
                pass
    os.makedirs(os.path.dirname(paths["history_db_path"]) or ".", exist_ok=True)
    with open(paths["history_db_path"], "w", encoding="utf-8") as f:
        json.dump({"videos": []}, f, indent=2, ensure_ascii=False)
    if clear_cache_db:
        clear_cache()
