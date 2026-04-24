import cv2
import os
import glob
import json
import hashlib

from core.frame_selection import run_frame_selection
from core.segment_builder import build_segments


PIXEL_DIFF_THRESH = 15
PERCENT_CHANGED_THRESH = 1.5
SUMMARY_FPS = 12
YOLO_MODEL_PATH = "models/yolov8n.pt"
YOLO_CONFIDENCE = 0.3
ALLOWED_CLASSES = {"person", "car"}
MERGE_GAP_SEC = 1.0
PRE_EVENT_SEC = 1.0
POST_EVENT_SEC = 2.0

WORKFLOW_STEPS = {
    "all": {
        "Loading video": {"progress": (2, 5), "subs": [
            "Reading video file",
            "Computing SHA-256 checksum",
            "Validating video format"
        ]},
        "Frame selection": {"progress": (5, 30), "subs": [
            "Opening video capture",
            "Processing frames for motion detection",
            "Selecting keyframes",
            "Saving selected frames"
        ]},
        "Keyframe extraction": {"progress": (30, 55), "subs": [
            "Reading keyframe images",
            "Creating thumbnails",
            "Writing frames to disk",
            "Building frame summary video"
        ]},
        "Segment building": {"progress": (55, 70), "subs": [
            "Analyzing frame timestamps",
            "Building temporal segments",
            "Merging nearby segments",
            "Saving segment data"
        ]},
        "Video reconstruction": {"progress": (70, 90), "subs": [
            "Extracting video segments",
            "Applying segment boundaries",
            "Writing reconstructed video",
            "Verifying output integrity"
        ]},
        "Finalizing output": {"progress": (90, 100), "subs": [
            "Updating cache database",
            "Writing metadata logs",
            "Verifying final output",
            "Complete!"
        ]},
    }
}


def _get_verbose_progress(step_name: str, sub_index: int, total_subs: int) -> tuple:
    """Calculate verbose progress percentage for a sub-step.
    
    Returns: (current_progress, step_name_with_detail)
    """
    step_data = WORKFLOW_STEPS["all"].get(step_name, {"progress": (0, 100), "subs": []})
    start_pct, end_pct = step_data["progress"]
    range_pct = end_pct - start_pct
    
    sub_pct = range_pct / total_subs
    current_pct = int(start_pct + (sub_index * sub_pct))
    detail = step_data["subs"][sub_index] if sub_index < len(step_data["subs"]) else ""
    
    return current_pct, f"{step_name}: {detail}"


def _notify_verbose(notify_fn, step_name: str, sub_index: int, total_subs: int):
    """Send verbose progress notification."""
    pct, detail = _get_verbose_progress(step_name, sub_index, total_subs)
    notify_fn(detail, pct)

CACHE_DB_PATH = os.path.abspath("data/summary_cache.json")


def _compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _load_cache_db() -> dict:
    """Load the cache database."""
    if os.path.exists(CACHE_DB_PATH):
        with open(CACHE_DB_PATH, "r") as f:
            return json.load(f)
    return {}


def _save_cache_db(db: dict):
    """Save the cache database."""
    os.makedirs(os.path.dirname(CACHE_DB_PATH), exist_ok=True)
    with open(CACHE_DB_PATH, "w") as f:
        json.dump(db, f, indent=4)


def _get_output_paths(video_name: str) -> dict:
    """Get all output paths for a video."""
    output_dir = os.path.abspath(os.path.join("data/outputs", video_name))
    summaries_dir = os.path.join(output_dir, "summaries")
    os.makedirs(summaries_dir, exist_ok=True)
    
    return {
        "output_dir": output_dir,
        "summaries_dir": summaries_dir,
        "frames_video": os.path.abspath(os.path.join(summaries_dir, "summary_frames.mp4")),
        "segments_video": os.path.abspath(os.path.join(summaries_dir, "summary_segments.mp4")),
    }


def is_cached(input_path: str) -> bool:
    """Check if summary already exists for this video using SHA-256 checksum."""
    checksum = _compute_sha256(input_path)
    db = _load_cache_db()
    if checksum in db:
        paths = db[checksum]
        return os.path.exists(paths["segments_video"])
    return False


def get_cached_result(input_path: str) -> dict:
    """Return cached result if available using SHA-256 checksum."""
    checksum = _compute_sha256(input_path)
    db = _load_cache_db()
    if checksum in db:
        paths = db[checksum]
        return {
            "frames_video": paths["frames_video"],
            "segments_video": paths["segments_video"],
            "output_dir": paths["output_dir"],
            "cached": True,
            "checksum": checksum,
        }
    raise ValueError("No cached result found")


def _save_to_cache(checksum: str, paths: dict):
    """Save video checksum and output paths to cache database."""
    db = _load_cache_db()
    db[checksum] = {
        "frames_video": paths["frames_video"],
        "segments_video": paths["segments_video"],
        "output_dir": paths["output_dir"],
    }
    _save_cache_db(db)


def _get_output_paths(video_name: str) -> dict:
    """Get all output paths for a video.
    
    Checks for legacy data/outputs path and migrates to results/ if found.
    """
    legacy_output = os.path.abspath(os.path.join("data/outputs", video_name))
    new_output = os.path.abspath(os.path.join("results", video_name))
    
    if os.path.exists(legacy_output) and not os.path.exists(new_output):
        import shutil
        shutil.move(legacy_output, new_output)
        output_dir = new_output
    else:
        output_dir = new_output
    
    summaries_dir = os.path.join(output_dir, "summaries")
    os.makedirs(summaries_dir, exist_ok=True)
    
    return {
        "output_dir": output_dir,
        "summaries_dir": summaries_dir,
        "frames_video": os.path.abspath(os.path.join(summaries_dir, "summary_frames.mp4")),
        "segments_video": os.path.abspath(os.path.join(summaries_dir, "summary_segments.mp4")),
    }


def is_cached(input_path: str) -> bool:
    """Check if summary already exists for this video using SHA-256 checksum."""
    checksum = _compute_sha256(input_path)
    db = _load_cache_db()
    if checksum in db:
        paths = db[checksum]
        return os.path.exists(paths["segments_video"])
    return False


def get_cached_result(input_path: str) -> dict:
    """Return cached result if available using SHA-256 checksum."""
    checksum = _compute_sha256(input_path)
    db = _load_cache_db()
    if checksum in db:
        paths = db[checksum]
        return {
            "frames_video": paths["frames_video"],
            "segments_video": paths["segments_video"],
            "output_dir": paths["output_dir"],
            "cached": True,
            "checksum": checksum,
        }
    raise ValueError("No cached result found")


def summarize_video(input_path: str, progress_callback=None) -> dict:
    """Runs full summarization pipeline on input video.
    
    Args:
        input_path: Path to input video file
        progress_callback: Optional callback function(step_name, progress) 
                      Called with current step info during processing
        
    Returns:
        dict with keys:
            - "frames_video": path to keyframe-based summary video
            - "segments_video": path to segment-based summary video
            - "output_dir": path to output directory
            - "cached": bool (True if result was cached)
            - "checksum": SHA-256 checksum of input video
    """
    input_path = os.path.abspath(input_path)
    
    checksum = _compute_sha256(input_path)
    db = _load_cache_db()
    if checksum in db:
        paths = db[checksum]
        return {
            "frames_video": paths["frames_video"],
            "segments_video": paths["segments_video"],
            "output_dir": paths["output_dir"],
            "cached": True,
            "checksum": checksum,
        }
    
    video_name = os.path.splitext(os.path.basename(input_path))[0]
    paths = _get_output_paths(video_name)
    
    def _notify(msg: str, progress: int):
        if progress_callback:
            progress_callback(msg, progress)
    
    _notify("تحميل الفيديو: قراءة الملف", 2)
    
    frame_selection_result = run_frame_selection(
        video_path=input_path,
        pixel_diff_thresh=PIXEL_DIFF_THRESH,
        percent_changed_thresh=PERCENT_CHANGED_THRESH,
        progress_callback=_notify
    )
    
    _notify("تحميل الفيديو: حساب البصمة", 4)
    
    _notify("اختيار الإطارات: معالجة الإطارات للكشف عن الحركة", 10)
    _notify("اختيار الإطارات: تحديد الإطارات الرئيسية", 20)
    
    frames_video_path = paths["frames_video"]
    summarize_frames_to_video(
        frames_dir=frame_selection_result["selected_dir"],
        output_video_path=frames_video_path,
        summary_fps=SUMMARY_FPS
    )
    
    _notify("استخراج الإطارات: بناء فيديو ملخص الإطارات", 40)
    
    segments = build_segments(
        selected_frames=frame_selection_result["selected_frames"],
        fps=frame_selection_result["fps"],
        merge_gap_sec=MERGE_GAP_SEC,
        pre_event_sec=PRE_EVENT_SEC,
        post_event_sec=POST_EVENT_SEC,
        total_frames=frame_selection_result["total_frames"]
    )
    
    _notify("بناء المقاطع: دمج المقاطع المتقاربة", 60)
    _notify("بناء المقاطع: حفظ بيانات المقاطع", 65)
    
    segments_video_path = paths["segments_video"]
    summarize_segments_to_video(
        video_path=input_path,
        segments=segments,
        output_video_path=segments_video_path,
        output_fps=frame_selection_result["fps"]
    )
    
    _notify("إعادة بناء الفيديو: استخراج مقاطع الفيديو", 75)
    _notify("إعادة بناء الفيديو: كتابة الفيديو المُعاد بناؤه", 85)
    
    logs_dir = os.path.join(paths["output_dir"], "logs")
    os.makedirs(logs_dir, exist_ok=True)
    with open(os.path.join(logs_dir, "segments.json"), "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=4)
    
    _notify("إنهاء المخرجات: تحديث قاعدة بيانات ذاكرة التخزين المؤقتة", 92)
    _notify("إنهاء المخرجات: كتابة سجلات البيانات الوصفية", 96)
    _notify("إنهاء المخرجات: اكتمل!", 100)
    
    _save_to_cache(checksum, paths)
    
    return {
        "frames_video": frames_video_path,
        "segments_video": segments_video_path,
        "output_dir": paths["output_dir"],
        "cached": False,
        "checksum": checksum,
    }

def get_sorted_frame_paths(frames_dir, extension="jpg"):
    # تحسين: ترتيب طبيعي للملفات لضمان عدم تداخل الإطارات (frame_10 قبل frame_2)
    frame_paths = sorted(glob.glob(os.path.join(frames_dir, f"*.{extension}")))
    if len(frame_paths) == 0:
        raise ValueError(f"No frames found in directory: {frames_dir}")
    return frame_paths

def initialize_video_writer(output_video_path, frame_size, fps, codec="mp4v"):
    output_video_path = os.path.abspath(output_video_path)
    if fps <= 0:
        fps = 24
    fourcc = cv2.VideoWriter_fourcc(*codec)
    writer = cv2.VideoWriter(output_video_path, fourcc, fps, frame_size)
    if not writer.isOpened():
        raise ValueError(f"Failed to open video writer for: {output_video_path}")
    return writer

def summarize_frames_to_video(frames_dir, output_video_path, summary_fps=None, image_extension="jpg"):
    """يحول الصور المختارة إلى فيديو ملخص سريع"""
    frame_paths = get_sorted_frame_paths(frames_dir, image_extension)
    first_frame = cv2.imread(frame_paths[0])
    height, width, _ = first_frame.shape
    
    fps = summary_fps if summary_fps and summary_fps > 0 else 24 

    video_writer = initialize_video_writer(output_video_path, (width, height), fps)
    
    for path in frame_paths:
        frame = cv2.imread(path)
        if frame is not None:
            video_writer.write(frame)
            
    video_writer.release()
    
    if not os.path.exists(output_video_path):
        raise IOError(f"Failed to create video: {output_video_path}")

def summarize_segments_to_video(video_path, segments, output_video_path, output_fps=None):
    """يستخرج المقاطع الأصلية ويدمجها بسلاسة تامة"""
    if not segments:
        raise ValueError("No segments provided for summarization.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    if source_fps <= 0: 
        source_fps = 25.0
    
    write_fps = output_fps if output_fps and output_fps > 0 else source_fps

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    video_writer = initialize_video_writer(output_video_path, (width, height), write_fps)

    for segment in segments:
        start_frame = int(segment["start_frame"])
        end_frame = int(segment["end_frame"])

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        current_frame = start_frame
        while current_frame <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            video_writer.write(frame)
            current_frame += 1

    video_writer.release()
    cap.release()
    
    if not os.path.exists(output_video_path):
        raise IOError(f"Failed to create video: {output_video_path}")
    print(f"Summary video saved: {output_video_path}")