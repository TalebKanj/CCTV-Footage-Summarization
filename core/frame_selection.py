
import cv2


import numpy as np
import os
from core.frame_preprocessing import preprocess_frame


def select_keyframes(
    cap,
    prev_gray,
    output_dir,
    pixel_diff_thresh,
    percent_changed_thresh,
    fps,
    total_frames=None,
    progress_callback=None,
    frame_skip=2
):

    frame_id = 1
    saved_frames = 0
    percent_changes = []
    selected_frames = []
    last_progress = 0
    skip_counter = 0

    kernel = np.ones((3, 3), np.uint8)

    while True:

        ret, frame = cap.read()

        if not ret:
            break
        
        skip_counter += 1
        if frame_skip > 1 and skip_counter < frame_skip:
            prev_gray = preprocess_frame(frame)
            frame_id += 1
            continue
        skip_counter = 0

        curr_gray = preprocess_frame(frame)

        diff = cv2.absdiff(prev_gray, curr_gray)

        _, motion_mask = cv2.threshold(
            diff,
            pixel_diff_thresh,
            255,
            cv2.THRESH_BINARY
        )

        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_DILATE, kernel)

        changed_pixels = np.count_nonzero(motion_mask)

        percent_changed = (changed_pixels / motion_mask.size) * 100

        percent_changes.append(percent_changed)

        if percent_changed > percent_changed_thresh:

            timestamp_sec = frame_id / fps if fps > 0 else 0.0

            filename = f"frame_{frame_id:06d}_chg_{percent_changed:.2f}.jpg"

            image_path = os.path.join(output_dir, filename)

            cv2.imwrite(image_path, frame)

            selected_frames.append({
                "frame_index": frame_id,
                "timestamp_sec": round(timestamp_sec, 3),
                "percent_changed": round(float(percent_changed), 3),
                "image_path": image_path
            })

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
    video_path,
    pixel_diff_thresh=15,
    percent_changed_thresh=0.15,
    progress_callback=None
):

    from core.frame_preprocessing import (
        video_preprocessing,
        preprocess_first_frame
    )

    setup = video_preprocessing(video_path)

    prev_gray = preprocess_first_frame(setup["cap"])

    percent_changes, saved_frames, selected_frames = select_keyframes(
        cap=setup["cap"],
        prev_gray=prev_gray,
        output_dir=setup["selected_dir"],
        pixel_diff_thresh=pixel_diff_thresh,
        percent_changed_thresh=percent_changed_thresh,
        fps=setup["fps"],
        total_frames=setup["total_frames"],
        progress_callback=progress_callback
    )

    return {
        "video_name": setup["video_name"],
        "total_frames": int(setup["total_frames"]),
        "saved_frames": saved_frames,
        "fps": float(setup["fps"]),
        "percent_changes": percent_changes,
        "selected_dir": setup["selected_dir"],
        "selected_frames": selected_frames
    }
