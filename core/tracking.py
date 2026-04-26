from __future__ import annotations

import json
import os
from typing import Callable, Optional

import cv2

from .config import load_config
from .utils.model_download import ensure_yolo_model


def _get_yolo_class():
    from ultralytics import YOLO  # Lazy import

    return YOLO


def load_tracking_model(
    model_path: str | None = None,
    progress_callback: Callable[[str, int], None] | None = None,
):
    cfg = load_config()
    if model_path is None:
        model_path = cfg.yolo_model_path

    model_path = ensure_yolo_model(
        progress_callback=progress_callback,
        model_path=model_path,
        model_repo=cfg.yolo_model_repo,
        model_filename=cfg.yolo_model_filename,
    )
    yolo = _get_yolo_class()
    return yolo(model_path)


def run_object_tracking_on_video(
    video_path: str,
    output_video_path: str,
    output_json_path: str,
    model,
    confidence: float = 0.5,
    allowed_classes: Optional[list[str]] = None,
    tracker_config: str = "custom_bytetrack.yaml",
):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 12.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    os.makedirs(os.path.dirname(output_video_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_json_path) or ".", exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    tracking_log = []
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(
            source=frame,
            persist=True,
            conf=confidence,
            tracker=tracker_config,
            verbose=False,
        )

        annotated_frame = frame.copy()

        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                boxes_xyxy = result.boxes.xyxy.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy()

                if result.boxes.id is not None:
                    track_ids = result.boxes.id.cpu().numpy().astype(int)
                else:
                    track_ids = [-1] * len(boxes_xyxy)

                confidences = result.boxes.conf.cpu().numpy()
                names = result.names

                for box, cls_id, track_id, conf_score in zip(boxes_xyxy, classes, track_ids, confidences):
                    cls_id = int(cls_id)
                    cls_name = names[cls_id]

                    if allowed_classes is not None and cls_name not in allowed_classes:
                        continue

                    x1, y1, x2, y2 = map(int, box)
                    timestamp_sec = frame_index / fps if fps > 0 else 0.0

                    label = f"{cls_name} ID:{int(track_id)} {float(conf_score):.2f}"
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        annotated_frame,
                        label,
                        (x1, max(25, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    tracking_log.append(
                        {
                            "frame_index": frame_index,
                            "timestamp_sec": round(timestamp_sec, 3),
                            "track_id": int(track_id),
                            "class_name": cls_name,
                            "confidence": round(float(conf_score), 4),
                            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                        }
                    )

        writer.write(annotated_frame)
        frame_index += 1

    writer.release()
    cap.release()

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(tracking_log, f, indent=4, ensure_ascii=False)

    return {
        "output_video_path": output_video_path,
        "output_json_path": output_json_path,
        "total_logged_objects": len(tracking_log),
    }

