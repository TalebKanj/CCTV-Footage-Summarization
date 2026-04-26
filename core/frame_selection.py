from __future__ import annotations

import os
from typing import Callable, Dict, List, Optional, Tuple

import cv2
import numpy as np

from .frame_preprocessing import preprocess_frame


def select_keyframes(
    cap: cv2.VideoCapture,
    prev_gray: np.ndarray,
    output_dir: str,
    pixel_diff_thresh: int,
    percent_changed_thresh: float,
    fps: float,
    total_frames: Optional[int] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
    frame_skip: int = 3,
    resize_width: int = 640,
    morph_kernel: int = 3,
    morph_close_iters: int = 1,
    morph_dilate_iters: int = 1,
    smoothing_window: int = 5,
) -> Tuple[List[float], int, List[Dict]]:
    frame_id = 1
    saved_frames = 0
    percent_changes: List[float] = []
    selected_frames: List[Dict] = []
    last_progress = 0
    skip_counter = 0

    # For temporal smoothing
    percent_history = []

    kernel = np.ones((max(1, morph_kernel), max(1, morph_kernel)), np.uint8)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        skip_counter += 1
        if frame_skip > 1 and skip_counter < frame_skip:
            prev_gray = preprocess_frame(frame, resize_width=resize_width)
            frame_id += 1
            continue
        skip_counter = 0

        curr_gray = preprocess_frame(frame, resize_width=resize_width)

        diff = cv2.absdiff(prev_gray, curr_gray)
        _, motion_mask = cv2.threshold(diff, pixel_diff_thresh, 255, cv2.THRESH_BINARY)

        if morph_close_iters > 0:
            motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_CLOSE, kernel, iterations=morph_close_iters)
        if morph_dilate_iters > 0:
            motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_DILATE, kernel, iterations=morph_dilate_iters)

        changed_pixels = np.count_nonzero(motion_mask)
        raw_percent_changed = (changed_pixels / motion_mask.size) * 100

        # Ignore very small isolated noise (e.g. less than 0.01%)
        if raw_percent_changed < 0.01:
            raw_percent_changed = 0.0

        percent_history.append(raw_percent_changed)
        if len(percent_history) > smoothing_window:
            percent_history.pop(0)

        # Moving average for temporal smoothing
        smoothed_percent_changed = sum(percent_history) / len(percent_history)
        percent_changes.append(float(smoothed_percent_changed))

        if smoothed_percent_changed > percent_changed_thresh:
            timestamp_sec = frame_id / fps if fps > 0 else 0.0
            filename = f"frame_{frame_id:06d}_chg_{smoothed_percent_changed:.2f}.jpg"
            image_path = os.path.join(output_dir, filename)
            cv2.imwrite(image_path, frame)

            selected_frames.append(
                {
                    "frame_index": frame_id,
                    "timestamp_sec": round(timestamp_sec, 3),
                    "percent_changed": round(float(smoothed_percent_changed), 3),
                    "image_path": image_path,
                }
            )
            saved_frames += 1

        prev_gray = curr_gray
        frame_id += 1

        if progress_callback and total_frames:
            progress = int((frame_id / total_frames) * 100)
            if progress >= last_progress + 5:
                last_progress = progress
                progress_callback(f"معالجة الإطار {frame_id}/{total_frames}", progress)

    cap.release()
    return percent_changes, saved_frames, selected_frames


def run_frame_selection(
    video_path: str,
    config: Optional[Dict] = None,
    pixel_diff_thresh: int = 15,
    percent_changed_thresh: float = 0.15,
    frame_skip: int = 3,
    resize_width: int = 640,
    morph_kernel: int = 3,
    morph_close_iters: int = 1,
    morph_dilate_iters: int = 1,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> Dict:
    """Run motion-based keyframe selection.

    Accepts either:
    - `config` dict with keys `pixel_diff_thresh`, `percent_changed_thresh`, `frame_skip`
    - or explicit keyword args.
    """
    from .frame_preprocessing import video_preprocessing, preprocess_first_frame

    if config:
        pixel_diff_thresh = int(config.get("pixel_diff_thresh", pixel_diff_thresh))
        percent_changed_thresh = float(config.get("percent_changed_thresh", percent_changed_thresh))
        frame_skip = int(config.get("frame_skip", frame_skip))
        resize_width = int(config.get("resize_width", resize_width))
        morph_kernel = int(config.get("morph_kernel", morph_kernel))
        # Handle backward compatibility with morph_open_iters config
        morph_close_iters = int(config.get("morph_open_iters", config.get("morph_close_iters", morph_close_iters)))
        morph_dilate_iters = int(config.get("morph_dilate_iters", morph_dilate_iters))

    setup = video_preprocessing(video_path)
    prev_gray = preprocess_first_frame(setup["cap"])

    percent_changes, saved_frames, selected_frames = select_keyframes(
        cap=setup["cap"],
        prev_gray=prev_gray,
        output_dir=setup["selected_dir"],
        pixel_diff_thresh=pixel_diff_thresh,
        percent_changed_thresh=percent_changed_thresh,
        fps=float(setup["fps"] or 0.0),
        total_frames=int(setup["total_frames"]) if setup.get("total_frames") is not None else None,
        progress_callback=progress_callback,
        frame_skip=frame_skip,
        resize_width=resize_width,
        morph_kernel=morph_kernel,
        morph_close_iters=morph_close_iters,
        morph_dilate_iters=morph_dilate_iters,
    )

    return {
        "video_name": setup["video_name"],
        "total_frames": int(setup["total_frames"]),
        "saved_frames": saved_frames,
        "fps": float(setup["fps"] or 0.0),
        "percent_changes": percent_changes,
        "selected_dir": setup["selected_dir"],
        "selected_frames": selected_frames,
    }
