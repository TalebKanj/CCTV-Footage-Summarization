import os
import cv2
import json
from ultralytics import YOLO


def load_tracking_model(model_path="yolov8n.pt"):
    return YOLO(model_path)


def run_object_tracking_on_video(
    video_path,
    output_video_path,
    output_json_path,
    model,
    confidence=0.5,
    allowed_classes=None,
    tracker_config="bytetrack.yaml"
):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 12.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

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
            verbose=False
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

                for box, cls_id, track_id, conf_score in zip(
                    boxes_xyxy, classes, track_ids, confidences
                ):
                    cls_id = int(cls_id)
                    cls_name = names[cls_id]

                    if allowed_classes is not None and cls_name not in allowed_classes:
                        continue

                    x1, y1, x2, y2 = map(int, box)
                    timestamp_sec = frame_index / fps if fps > 0 else 0.0

                    label = f"{cls_name} ID:{track_id} {conf_score:.2f}"
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        annotated_frame,
                        label,
                        (x1, max(25, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

                    tracking_log.append({
                        "frame_index": frame_index,
                        "timestamp_sec": round(timestamp_sec, 3),
                        "track_id": int(track_id),
                        "class_name": cls_name,
                        "confidence": round(float(conf_score), 4),
                        "bbox": {
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2
                        }
                    })

        writer.write(annotated_frame)
        frame_index += 1

    writer.release()
    cap.release()

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(tracking_log, f, indent=4)

    return {
        "output_video_path": output_video_path,
        "output_json_path": output_json_path,
        "total_logged_objects": len(tracking_log)
    }