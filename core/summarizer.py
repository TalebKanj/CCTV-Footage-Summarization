from __future__ import annotations

import glob
import hashlib
import json
import os
import re
from typing import Any, Callable, Dict, List, Optional, Union

import cv2
import numpy as np

from .config import AppConfig, config_from_overrides, load_config
from .frame_selection import run_frame_selection
from .segment_builder import build_segments
from .object_detection import load_yolo_model, run_object_detection_on_frames, frames_to_video


def _compute_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def _config_fingerprint(cfg: AppConfig) -> str:
    """Stable hash of summarization-relevant options; used to invalidate cache when options change."""

    def _norm_classes(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [p.strip() for p in value.split(",") if p.strip()]
        if isinstance(value, (set, tuple, list)):
            return [str(x).strip() for x in value if str(x).strip()]
        return [str(value).strip()]

    payload = {
        "pixel_diff_thresh": int(cfg.pixel_diff_thresh),
        "percent_changed_thresh": float(cfg.percent_changed_thresh),
        "frame_skip": int(cfg.frame_skip),
        "resize_width": int(getattr(cfg, "resize_width", 640)),
        "morph_kernel": int(getattr(cfg, "morph_kernel", 5)),
        "morph_open_iters": int(getattr(cfg, "morph_open_iters", 2)),
        "morph_dilate_iters": int(getattr(cfg, "morph_dilate_iters", 2)),
        "summary_fps": int(cfg.summary_fps),
        "merge_gap_sec": float(cfg.merge_gap_sec),
        "pre_event_sec": float(cfg.pre_event_sec),
        "post_event_sec": float(cfg.post_event_sec),
        "enable_object_detection": bool(getattr(cfg, "enable_object_detection", False)),
        "yolo_confidence": float(cfg.yolo_confidence),
        "allowed_classes": _norm_classes(cfg.allowed_classes),
        "yolo_model_path": str(getattr(cfg, "yolo_model_path", "")),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_cache_db(db_path: str) -> Dict[str, dict]:
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
            return db if isinstance(db, dict) else {}
        except Exception:
            return {}
    return {}


def _save_cache_db(db_path: str, db: Dict[str, dict]) -> None:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


def _resolve_output_paths(video_name: str, output_base: str, variant: Optional[str] = None) -> Dict[str, str]:
    # Keep runs separated when options change so history doesn't get overwritten.
    if variant:
        base_dir = os.path.abspath(os.path.join(output_base, video_name, variant))
    else:
        base_dir = os.path.abspath(os.path.join(output_base, video_name))
    selected_dir = os.path.join(base_dir, "selected_frames")
    detected_dir = os.path.join(base_dir, "detected_frames")
    summaries_dir = os.path.join(base_dir, "summaries")
    logs_dir = os.path.join(base_dir, "logs")

    os.makedirs(selected_dir, exist_ok=True)
    os.makedirs(detected_dir, exist_ok=True)
    os.makedirs(summaries_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    return {
        "base_dir": base_dir,
        "selected_dir": selected_dir,
        "detected_dir": detected_dir,
        "summaries_dir": summaries_dir,
        "logs_dir": logs_dir,
        "frames_video": os.path.join(summaries_dir, "summary_frames.mp4"),
        "segments_video": os.path.join(summaries_dir, "summary_segments.mp4"),
        "detected_video": os.path.join(summaries_dir, "summary_detected.mp4"),
    }


def natural_sort_key(s: str) -> List[Union[int, str]]:
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]


def get_sorted_frame_paths(frames_dir: str, extension: str = "jpg") -> List[str]:
    frame_paths = glob.glob(os.path.join(frames_dir, f"*.{extension}"))
    frame_paths.sort(key=natural_sort_key)
    if not frame_paths:
        raise ValueError(f"No frames found in directory: {frames_dir}")
    return frame_paths


def summarize_frames_to_video(frames_dir: str, output_video_path: str, summary_fps: int = 12) -> None:
    frame_paths = get_sorted_frame_paths(frames_dir)
    first_image = cv2.imread(frame_paths[0])
    if first_image is None:
        raise ValueError(f"Unable to read frame: {frame_paths[0]}")

    height, width = first_image.shape[:2]
    os.makedirs(os.path.dirname(output_video_path) or ".", exist_ok=True)

    writer = cv2.VideoWriter(
        output_video_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        summary_fps,
        (width, height),
    )

    previous_frame = None
    for path in frame_paths:
        frame = cv2.imread(path)
        if frame is None:
            continue
            
        if previous_frame is not None:
            # Alpha blending: 0.5 * previous + 0.5 * current
            blended = cv2.addWeighted(previous_frame, 0.5, frame, 0.5, 0)
            writer.write(blended)
        else:
            writer.write(frame)
            
        previous_frame = frame

    writer.release()


def summarize_segments_to_video(
    video_path: str,
    segments: List[Dict[str, float]],
    output_video_path: str,
    output_fps: int = 12,
) -> None:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    if output_fps <= 0 or np.isnan(output_fps):
        output_fps = 25

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = None
    current_frame = 0
    segments = sorted(list(segments), key=lambda segment: segment["start_frame"])

    while segments:
        segment = segments.pop(0)
        start = int(segment["start_frame"])
        end = int(segment["end_frame"])

        if current_frame > end:
            continue

        if current_frame < start:
            frames_to_skip = start - current_frame
            if frames_to_skip < 30:
                for _ in range(frames_to_skip):
                    cap.read()
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, start)
            current_frame = start

        if writer is None:
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            os.makedirs(os.path.dirname(output_video_path) or ".", exist_ok=True)
            writer = cv2.VideoWriter(output_video_path, fourcc, output_fps, (frame_width, frame_height))
            if not writer.isOpened():
                raise ValueError("Video writer failed to open")

        while current_frame <= end:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
                
            writer.write(frame)
            current_frame += 1

    if writer:
        writer.release()
    cap.release()


def is_cached(input_path: str, config: Optional[AppConfig] = None) -> bool:
    config = config or load_config()
    checksum = _compute_sha256(os.path.abspath(input_path))
    cfg_hash = _config_fingerprint(config)
    db = _load_cache_db(config.cache_db_path)
    key = f"{checksum}:{cfg_hash}"
    if key in db and os.path.exists((db[key] or {}).get("segments_video", "")):
        return True
    legacy = db.get(checksum) or {}
    if legacy and os.path.exists(legacy.get("segments_video", "")):
        meta = legacy.get("meta") or {}
        if isinstance(meta, dict) and meta.get("config_hash") == cfg_hash:
            return True
    return False


def get_cached_result(input_path: str, config: Optional[AppConfig] = None) -> Dict[str, object]:
    config = config or load_config()
    checksum = _compute_sha256(os.path.abspath(input_path))
    cfg_hash = _config_fingerprint(config)
    db = _load_cache_db(config.cache_db_path)

    key = f"{checksum}:{cfg_hash}"
    paths = db.get(key)
    if not isinstance(paths, dict):
        legacy = db.get(checksum)
        if isinstance(legacy, dict):
            meta = legacy.get("meta") or {}
            if isinstance(meta, dict) and meta.get("config_hash") == cfg_hash:
                paths = legacy

    if not isinstance(paths, dict):
        raise ValueError("No cached result found")

    result: Dict[str, object] = {
        "frames_video": paths.get("frames_video"),
        "segments_video": paths.get("segments_video"),
        "detected_video": paths.get("detected_video"),
        "selected_dir": paths.get("selected_dir", ""),
        "output_dir": paths.get("output_dir"),
        "cached": True,
        "checksum": checksum,
    }
    meta = paths.get("meta")
    if isinstance(meta, dict):
        result.update(meta)
    if "video_name" not in result and paths.get("video_name"):
        result["video_name"] = paths.get("video_name")
    return result


def _save_to_cache(checksum: str, result: Dict[str, object], config: AppConfig) -> None:
    cfg_hash = _config_fingerprint(config)
    cache_key = f"{checksum}:{cfg_hash}"
    db = _load_cache_db(config.cache_db_path)
    db[cache_key] = {
        "input_checksum": checksum,
        "config_hash": cfg_hash,
        "video_name": result.get("video_name"),
        "frames_video": result.get("frames_video"),
        "segments_video": result.get("segments_video"),
        "detected_video": result.get("detected_video"),
        "selected_dir": result.get("selected_dir"),
        "output_dir": result.get("output_dir"),
        "meta": {
            "config_hash": cfg_hash,
            "fps": result.get("fps"),
            "total_frames": result.get("total_frames"),
            "selected_frames_count": result.get("selected_frames_count"),
            "frames_reduced_pct": result.get("frames_reduced_pct"),
            "segments_count": result.get("segments_count"),
            "duration_sec": result.get("duration_sec"),
            "config_snapshot": result.get("config_snapshot"),
        },
    }
    _save_cache_db(config.cache_db_path, db)


def summarize_video(
    input_path: str,
    config: Optional[Union[AppConfig, Dict]] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> Dict[str, object]:
    """Main API: motion frame selection → segments → summary videos.

    Accepts `config` as either AppConfig or dict overrides.
    """
    if isinstance(config, dict) or config is None:
        cfg = config_from_overrides(config, base=None)
    else:
        cfg = config

    input_path = os.path.abspath(input_path)
    checksum = _compute_sha256(input_path)

    cache_db = _load_cache_db(cfg.cache_db_path)
    cfg_hash = _config_fingerprint(cfg)
    cache_key = f"{checksum}:{cfg_hash}"

    # Cache is keyed by (input checksum + config hash). This guarantees re-summarization when options change.
    if cache_key in cache_db:
        cached_segments = (cache_db.get(cache_key) or {}).get("segments_video", "")
        if cached_segments and os.path.exists(cached_segments):
            print(f"[DEBUG] Cache hit: {os.path.basename(input_path)} ({checksum[:12]}:{cfg_hash[:8]})")
            return get_cached_result(input_path, config=cfg)
        # Stale cache entry: remove it so we can recompute.
        try:
            del cache_db[cache_key]
            _save_cache_db(cfg.cache_db_path, cache_db)
            print(f"[DEBUG] Stale cache removed: {os.path.basename(input_path)} ({checksum[:12]}:{cfg_hash[:8]})")
        except Exception:
            pass

    video_name = os.path.splitext(os.path.basename(input_path))[0]
    paths = _resolve_output_paths(video_name, cfg.output_base, variant=cfg_hash[:8])

    def notify(label: str, progress: int) -> None:
        if progress_callback:
            progress_callback(label, progress)

    notify("تحميل الفيديو: يتم تجهيز الملف", 2)
    frame_selection_result = run_frame_selection(
        video_path=input_path,
        pixel_diff_thresh=cfg.pixel_diff_thresh,
        percent_changed_thresh=cfg.percent_changed_thresh,
        frame_skip=cfg.frame_skip,
        resize_width=getattr(cfg, "resize_width", 640),
        morph_kernel=getattr(cfg, "morph_kernel", 3),
        morph_close_iters=getattr(cfg, "morph_open_iters", 1),
        morph_dilate_iters=getattr(cfg, "morph_dilate_iters", 1),
        progress_callback=notify,
    )

    notify("اختيار الإطارات: يتم تسجيل الإطارات المحددة", 40)
    summarize_frames_to_video(
        frames_dir=frame_selection_result["selected_dir"],
        output_video_path=paths["frames_video"],
        summary_fps=int(cfg.summary_fps),
    )

    detected_video_path = None
    if getattr(cfg, "enable_object_detection", False):
        notify("الكشف الذكي: تحميل نموذج YOLO", 45)
        model = load_yolo_model(
            progress_callback=notify,
            model_path=cfg.yolo_model_path,
            model_repo=getattr(cfg, "yolo_model_repo", "Ultralytics/YOLOv8"),
            model_filename=getattr(cfg, "yolo_model_filename", "yolov8x.pt"),
            hf_token=getattr(cfg, "hf_token", None),
        )

        notify("الكشف الذكي: معالجة الإطارات المحددة", 55)
        run_object_detection_on_frames(
            frames_dir=frame_selection_result["selected_dir"],
            output_dir=paths["detected_dir"],
            model=model,
            config={
                "yolo_confidence": cfg.yolo_confidence,
                "allowed_classes": cfg.allowed_classes,
            },
        )

        notify("الكشف الذكي: إنشاء فيديو المعاينة", 58)
        detected_video_path = paths["detected_video"]
        frames_to_video(paths["detected_dir"], detected_video_path, fps=int(cfg.summary_fps))

    notify("بناء المقاطع: تحديد مقاطع الحركة", 60)
    segments = build_segments(
        selected_frames=frame_selection_result.get("selected_frames", []),
        fps=frame_selection_result.get("fps") or float(cfg.summary_fps),
        merge_gap_sec=float(cfg.merge_gap_sec),
        pre_event_sec=float(cfg.pre_event_sec),
        post_event_sec=float(cfg.post_event_sec),
        total_frames=frame_selection_result.get("total_frames"),
    )

    notify("إعادة بناء الفيديو: حفظ ملف الملخص النهائي", 80)
    summarize_segments_to_video(
        video_path=input_path,
        segments=segments,
        output_video_path=paths["segments_video"],
        output_fps=int(frame_selection_result.get("fps") or cfg.summary_fps),
    )

    os.makedirs(paths["logs_dir"], exist_ok=True)
    with open(os.path.join(paths["logs_dir"], "segments.json"), "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=4, ensure_ascii=False)

    notify("اكتملت عملية الملخص بنجاح", 100)

    total_frames = int(frame_selection_result.get("total_frames") or 0)
    selected_count = int(frame_selection_result.get("saved_frames") or 0)
    frames_reduced_pct = round((1.0 - (selected_count / total_frames)) * 100.0, 2) if total_frames > 0 else 0.0
    fps = float(frame_selection_result.get("fps") or cfg.summary_fps)
    duration_sec = round(total_frames / fps, 3) if fps > 0 and total_frames > 0 else None

    result = {
        "frames_video": paths["frames_video"],
        "segments_video": paths["segments_video"],
        "detected_video": detected_video_path,
        "selected_dir": paths["selected_dir"],
        "output_dir": paths["base_dir"],
        "cached": False,
        "checksum": checksum,
        "video_name": video_name,
        "fps": fps,
        "total_frames": total_frames,
        "selected_frames_count": selected_count,
        "frames_reduced_pct": frames_reduced_pct,
        "segments_count": len(segments),
        "duration_sec": duration_sec,
        "config_snapshot": {
            "pixel_diff_thresh": cfg.pixel_diff_thresh,
            "percent_changed_thresh": cfg.percent_changed_thresh,
            "frame_skip": cfg.frame_skip,
            "resize_width": getattr(cfg, "resize_width", 640),
            "morph_kernel": getattr(cfg, "morph_kernel", 3),
            "morph_open_iters": getattr(cfg, "morph_open_iters", 1),
            "morph_dilate_iters": getattr(cfg, "morph_dilate_iters", 1),
            "summary_fps": cfg.summary_fps,
            "merge_gap_sec": cfg.merge_gap_sec,
            "pre_event_sec": cfg.pre_event_sec,
            "post_event_sec": cfg.post_event_sec,
            "yolo_confidence": cfg.yolo_confidence,
            "allowed_classes": list(cfg.allowed_classes),
            "enable_object_detection": getattr(cfg, "enable_object_detection", False),
        },
    }
    try:
        _save_to_cache(checksum, result, cfg)
    except Exception:
        pass
    return result


def clear_cache(config: Optional[Union[AppConfig, Dict]] = None) -> None:
    if isinstance(config, AppConfig):
        cfg = config
    else:
        cfg = config_from_overrides(config if isinstance(config, dict) else None, base=None)
    if os.path.exists(cfg.cache_db_path):
        os.remove(cfg.cache_db_path)
