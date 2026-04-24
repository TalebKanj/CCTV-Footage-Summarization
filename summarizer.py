import cv2
import os
import glob


def get_sorted_frame_paths(frames_dir, extension="jpg"):
    frame_paths = sorted(glob.glob(os.path.join(frames_dir, f"*.{extension}")))
    if len(frame_paths) == 0:
        raise ValueError(f"No frames found in directory: {frames_dir}")
    return frame_paths


def initialize_video_writer(output_video_path, frame_size, fps, codec="mp4v"):
    fourcc = cv2.VideoWriter_fourcc(*codec)
    return cv2.VideoWriter(output_video_path, fourcc, fps, frame_size)


def write_frames_to_video(video_writer, frame_paths):
    for path in frame_paths:
        frame = cv2.imread(path)
        video_writer.write(frame)
    video_writer.release()


def summarize_frames_to_video(frames_dir, output_video_path, summary_fps=12, image_extension="jpg"):
    frame_paths = get_sorted_frame_paths(frames_dir, image_extension)
    first_frame = cv2.imread(frame_paths[0])
    height, width, _ = first_frame.shape
    video_writer = initialize_video_writer(
        output_video_path,
        (width, height),
        summary_fps
    )
    write_frames_to_video(video_writer, frame_paths)


def summarize_segments_to_video(video_path, segments, output_video_path, output_fps=None):
    if not segments:
        raise ValueError("No segments provided for summarization.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    if source_fps <= 0:
        source_fps = 12.0

    write_fps = output_fps if output_fps is not None else source_fps

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    video_writer = initialize_video_writer(
        output_video_path,
        (width, height),
        write_fps
    )

    for segment in segments:
        start_frame = segment["start_frame"]
        end_frame = segment["end_frame"]

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