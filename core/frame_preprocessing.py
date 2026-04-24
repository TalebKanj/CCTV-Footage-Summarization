
import os
import cv2

def video_preprocessing(video_path, base_output="results"):

    video_name = os.path.splitext(os.path.basename(video_path))[0]

    base_dir = os.path.join(base_output, video_name)
    selected_dir = os.path.join(base_dir, "selected_frames")

    os.makedirs(selected_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    metadata = {
        "video_name": video_name,
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "cap": cap,
        "selected_dir": selected_dir
    }

    return metadata


def preprocess_frame(frame, resize_width=640):

    h, w = frame.shape[:2]

    if w > resize_width:
        scale = resize_width / w
        frame = cv2.resize(frame, (resize_width, int(h * scale)))

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    return gray


def preprocess_first_frame(cap):

    ret, first_frame = cap.read()

    if not ret:
        raise ValueError("Could not read first frame")

    prev_gray = preprocess_frame(first_frame)

    return prev_gray
