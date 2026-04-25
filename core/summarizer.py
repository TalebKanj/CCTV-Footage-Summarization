import glob
import hashlib
import json
import os
from typing import Callable, Dict, List, Optional

import cv2

from core.config import AppConfig, load_config
from core.frame_selection import run_frame_selection
from core.segment_builder import build_segments


def _compute_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def _load_cache_db(db_path: str) -> Dict[str, dict]:
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache_db(db_path: str, db: Dict[str, dict]) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)


def _resolve_output_paths(video_name: str, output_base: str) -> Dict[str, str]:
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
    }


def get_sorted_frame_paths(frames_dir: str, extension: str = "jpg") -> List[str]:
    frame_paths = sorted(glob.glob(os.path.join(frames_dir, f"*.{extension}")))
    if not frame_paths:
        raise ValueError(f"No frames found in directory: {frames_dir}")
    return frame_paths


def summarize_frames_to_video(frames_dir: str, output_video_path: str, summary_fps: int = 12) -> None:
    frame_paths = get_sorted_frame_paths(frames_dir)
    first_image = cv2.imread(frame_paths[0])
    if first_image is None:
        raise ValueError(f"Unable to read frame: {frame_paths[0]}")

    height, width = first_image.shape[:2]
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

    writer = cv2.VideoWriter(
        output_video_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        summary_fps,
        (width, height)
    )

    for path in frame_paths:
        frame = cv2.imread(path)
        if frame is None:
            continue
        writer.write(frame)

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

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = None
    current_frame = 0
    segments = sorted(segments, key=lambda segment: segment["start_frame"])

    while segments:
        segment = segments.pop(0)
        start = int(segment["start_frame"])
        end = int(segment["end_frame"])

        if current_frame > end:
            continue

        if current_frame < start:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start)
            current_frame = start

        if writer is None:
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            writer = cv2.VideoWriter(output_video_path, fourcc, output_fps, (frame_width, frame_height))

        while current_frame <= end:
            ret, frame = cap.read()
            if not ret:
                break
            writer.write(frame)
            current_frame += 1

    if writer:
        writer.release()
    cap.release()


def is_cached(input_path: str, config: Optional[AppConfig] = None) -> bool:
    config = config or load_config()
    checksum = _compute_sha256(os.path.abspath(input_path))
    db = _load_cache_db(config.cache_db_path)
    return checksum in db and os.path.exists(db[checksum].get("segments_video", ""))


def get_cached_result(input_path: str, config: Optional[AppConfig] = None) -> Dict[str, str]:
    config = config or load_config()
    checksum = _compute_sha256(os.path.abspath(input_path))
    db = _load_cache_db(config.cache_db_path)

    if checksum not in db:
        raise ValueError("No cached result found")

    paths = db[checksum]
    return {
        "frames_video": paths["frames_video"],
        "segments_video": paths["segments_video"],
        "output_dir": paths["output_dir"],
        "cached": True,
        "checksum": checksum,
    }


def _save_to_cache(checksum: str, paths: Dict[str, str], config: AppConfig) -> None:
    db = _load_cache_db(config.cache_db_path)
    db[checksum] = {
        "frames_video": paths["frames_video"],
        "segments_video": paths["segments_video"],
        "output_dir": paths["base_dir"],
    }
    _save_cache_db(config.cache_db_path, db)


def summarize_video(
    input_path: str,
    config: Optional[AppConfig] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> Dict[str, object]:
    config = config or load_config()
    input_path = os.path.abspath(input_path)
    checksum = _compute_sha256(input_path)

    if checksum in _load_cache_db(config.cache_db_path):
        return get_cached_result(input_path, config=config)

    paths = _resolve_output_paths(os.path.splitext(os.path.basename(input_path))[0], config.output_base)

    def notify(label: str, progress: int) -> None:
        if progress_callback:
            progress_callback(label, progress)

    notify("تحميل الفيديو: يتم تجهيز الملف", 2)
    frame_selection_result = run_frame_selection(
        video_path=input_path,
        pixel_diff_thresh=config.pixel_diff_thresh,
        percent_changed_thresh=config.percent_changed_thresh,
        progress_callback=notify,
    )

    notify("اختيار الإطارات: يتم تسجيل الإطارات المحددة", 40)
    summarize_frames_to_video(
        frames_dir=frame_selection_result["selected_dir"],
        output_video_path=paths["frames_video"],
        summary_fps=config.summary_fps,
    )

    notify("بناء المقاطع: تحديد مقاطع الحركة", 60)
    segments = build_segments(
        selected_frames=frame_selection_result["selected_frames"],
        fps=frame_selection_result["fps"],
        merge_gap_sec=config.merge_gap_sec,
        pre_event_sec=config.pre_event_sec,
        post_event_sec=config.post_event_sec,
        total_frames=frame_selection_result["total_frames"],
    )

    notify("إعادة بناء الفيديو: حفظ ملف الملخص النهائي", 80)
    summarize_segments_to_video(
        video_path=input_path,
        segments=segments,
        output_video_path=paths["segments_video"],
        output_fps=int(frame_selection_result["fps"] or config.summary_fps),
    )

    os.makedirs(paths["logs_dir"], exist_ok=True)
    with open(os.path.join(paths["logs_dir"], "segments.json"), "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=4)

    _save_to_cache(checksum, paths, config)
    notify("اكتملت عملية الملخص بنجاح", 100)

    return {
        "frames_video": paths["frames_video"],
        "segments_video": paths["segments_video"],
        "output_dir": paths["base_dir"],
        "cached": False,
        "checksum": checksum,
    }


def clear_cache(config: Optional[AppConfig] = None) -> None:
    config = config or load_config()
    if os.path.exists(config.cache_db_path):
        os.remove(config.cache_db_path)
