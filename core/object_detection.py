from ultralytics import YOLO
import os
import glob
import cv2
import torch

from core.gpu_memory import clear_gpu_cache


def _select_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def get_sorted_frame_paths(frames_dir: str) -> list[str]:
    frame_paths = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))
    if not frame_paths:
        raise ValueError(f"No frames found in directory: {frames_dir}")
    return frame_paths


def load_yolo_model(model_path: str = "yolov8n.pt", device: str | None = None):
    clear_gpu_cache()
    if device is None:
        device = _select_device()
    return YOLO(model_path, device=device)


def run_object_detection_on_frames(
    frames_dir: str,
    output_dir: str,
    model,
    confidence: float = 0.5,
    allowed_classes: list[str] | None = None,
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    frame_paths = get_sorted_frame_paths(frames_dir)
    results = model(frame_paths, conf=confidence)

    for path, result in zip(frame_paths, results):
        image = cv2.imread(path)
        if image is None:
            continue

        for box in result.boxes:
            cls_id = int(box.cls)
            cls_name = result.names[cls_id]
            if allowed_classes and cls_name not in allowed_classes:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf)
            label = f"{cls_name} {conf:.2f}"

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                image,
                label,
                (x1, max(y1 - 10, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        filename = os.path.basename(path)
        cv2.imwrite(os.path.join(output_dir, filename), image)
