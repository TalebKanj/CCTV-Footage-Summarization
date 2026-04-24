from frame_selection import run_frame_selection
from summarizer import summarize_frames_to_video, summarize_segments_to_video
from object_detection import run_object_detection_on_frames, load_yolo_model
from segment_builder import build_segments
from tracking import load_tracking_model, run_object_tracking_on_video
import os
import json


VIDEO_PATH = "Videos/test.mp4"

PIXEL_DIFF_THRESH = 15
PERCENT_CHANGED_THRESH = 0.15

SUMMARY_FPS = 12
YOLO_MODEL_PATH = "yolov8n.pt"
YOLO_CONFIDENCE = 0.3
ALLOWED_CLASSES = {"person", "car"}

MERGE_GAP_SEC = 2.0
PRE_EVENT_SEC = 2.0
POST_EVENT_SEC = 4.0


def main():
    frame_selection_result = run_frame_selection(
        video_path=VIDEO_PATH,
        pixel_diff_thresh=PIXEL_DIFF_THRESH,
        percent_changed_thresh=PERCENT_CHANGED_THRESH
    )

    base_dir = os.path.dirname(frame_selection_result["selected_dir"])
    selected_frames_dir = frame_selection_result["selected_dir"]
    detected_frames_dir = os.path.join(base_dir, "detected_frames")
    summaries_dir = os.path.join(base_dir, "summaries")
    logs_dir = os.path.join(base_dir, "logs")

    os.makedirs(detected_frames_dir, exist_ok=True)
    os.makedirs(summaries_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    summarize_frames_to_video(
        frames_dir=selected_frames_dir,
        output_video_path=os.path.join(summaries_dir, "summary_raw_frames.mp4"),
        summary_fps=SUMMARY_FPS
    )

    segments = build_segments(
        selected_frames=frame_selection_result["selected_frames"],
        fps=frame_selection_result["fps"],
        merge_gap_sec=MERGE_GAP_SEC,
        pre_event_sec=PRE_EVENT_SEC,
        post_event_sec=POST_EVENT_SEC,
        total_frames=frame_selection_result["total_frames"]
    )

    summarize_segments_to_video(
        video_path=VIDEO_PATH,
        segments=segments,
        output_video_path=os.path.join(summaries_dir, "summary_raw_segments.mp4"),
        output_fps=frame_selection_result["fps"]
    )

    with open(os.path.join(logs_dir, "segments.json"), "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=4)

    model = load_yolo_model(YOLO_MODEL_PATH)

    run_object_detection_on_frames(
        frames_dir=selected_frames_dir,
        output_dir=detected_frames_dir,
        model=model,
        confidence=YOLO_CONFIDENCE,
        allowed_classes=ALLOWED_CLASSES
    )

    summarize_frames_to_video(
        frames_dir=detected_frames_dir,
        output_video_path=os.path.join(summaries_dir, "summary_detected_frames.mp4"),
        summary_fps=SUMMARY_FPS
    )

    tracking_video_path = os.path.join(summaries_dir, "summary_tracked_full.mp4")
    tracking_json_path = os.path.join(logs_dir, "tracking_log.json")

    tracking_model = load_tracking_model(YOLO_MODEL_PATH)

    tracking_result = run_object_tracking_on_video(
        video_path=VIDEO_PATH,
        output_video_path=tracking_video_path,
        output_json_path=tracking_json_path,
        model=tracking_model,
        confidence=YOLO_CONFIDENCE,
        allowed_classes=ALLOWED_CLASSES,
        tracker_config="custom_bytetrack.yaml"
    )

    print("Tracking finished:")
    print(tracking_result)


if __name__ == "__main__":
    main()