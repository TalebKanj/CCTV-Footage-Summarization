from ultralytics import YOLO
import os
import glob
import cv2
from core.gpu_memory import clear_gpu_cache


def get_sorted_frame_paths(frames_dir):

    frame_paths = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))

    if not frame_paths:
        raise ValueError("No frames found")

    return frame_paths


def load_yolo_model(model_path="yolov8n.pt"):
    clear_gpu_cache()
    return YOLO(model_path)


def run_object_detection_on_frames(
    frames_dir,
    output_dir,
    model,
    confidence=0.5,
    allowed_classes=None
):

    os.makedirs(output_dir, exist_ok=True)

    frame_paths = get_sorted_frame_paths(frames_dir)

    results = model(frame_paths, conf=confidence)

    for path, result in zip(frame_paths, results):

        image = cv2.imread(path)

        for box in result.boxes:

            cls_id = int(box.cls)

            cls_name = result.names[cls_id]

            if allowed_classes and cls_name not in allowed_classes:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            conf = float(box.conf)

            label = f"{cls_name} {conf:.2f}"

            cv2.rectangle(image, (x1, y1), (x2, y2), (0,255,0), 2)

            cv2.putText(
                image,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0,255,0),
                2
            )

        filename = os.path.basename(path)

        cv2.imwrite(os.path.join(output_dir, filename), image)
