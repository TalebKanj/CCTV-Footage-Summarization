# AGENTS.md

## Running the Project

```bash
# CLI (legacy pipeline)
python app/main.py

# Streamlit UI (recommended)
streamlit run app/ui.py
```

## Prerequisites

1. Place input video at `data/inputs/test.mp4` (or use UI upload)
2. Download `yolov8n.pt` from https://docs.ultralytics.com/ and place in `models/`
3. Install dependencies: `pip install opencv-python ultralytics numpy matplotlib streamlit`

## Output Structure

All outputs go to `results/{video-name}/`:

```
results/{video-name}/
├── selected_frames/     # Motion-keyframe JPEGs
├── summaries/
│   ├── summary_frames.mp4       # Keyframe-based summary
│   └── summary_segments.mp4    # Segment-based summary (main output)
├── detected_frames/   # YOLO annotated frames
└── logs/
    └── segments.json  # Segment metadata
```

## Key Configuration

Edit in `app/config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `pixel_diff_thresh` | 25 | MOG2 varThreshold |
| `percent_changed_thresh` | 0.15 | % motion pixels to keep frame |
| `summary_fps` | 12 | Output video FPS |
| `yolo_confidence` | 0.3 | YOLO detection confidence |
| `allowed_classes` | ["person", "car"] | Classes to detect |
| `merge_gap_sec` | 2.0 | Merge segments within gap |
| `pre_event_sec` | 2.0 | Pre-event padding |
| `post_event_sec` | 4.0 | Post-event padding |

## MOG2 Settings (core/frame_selection.py)

| Parameter | Value | Note |
|-----------|-------|------|
| `history` | 500 | Frames in background model |
| `varThreshold` | 25 | Changed from 15 for stability |
| `detectShadows` | False | Disabled for CCTV performance |
| `buffer_duration_sec` | 1.5 | Motion buffer prevents flicker |

## Architecture

Two code versions:
- `app/` + `core/` - Uses MOG2 background subtraction (recommended)
- Root modules - Uses simple frame differencing (legacy)

## UI Features

Streamlit UI (`app/ui.py`) with:
- Syrian-inspired theme (red `#CE1126`, gold `#B9A779`)
- Theme toggle (dark/light)
- SHA-256 content hashing for duplicate detection
- Real-time progress bar
- Cache system reuses previous results

## Cache System

- Cache database: `data/summary_cache.json`
- Uses SHA-256 hash of file content
- Works even if user renames video file
- Force re-process available in UI

## Module Overview

- `app/main.py` - CLI orchestrator
- `app/ui.py` - Streamlit UI
- `app/config.py` - Centralized configuration
- `app/theme.py` - Theme utilities
- `app/styles.css` - Component styles
- `core/frame_selection.py` - MOG2 motion detection
- `core/object_detection.py` - YOLOv8 detection
- `core/tracking.py` - ByteTrack object tracking
- `core/summarizer.py` - Frames → video + caching
- `core/segment_builder.py` - Temporal segments
- `core/frame_preprocessing.py` - Video I/O

## Notes

- No test suite exists
- No lint/typecheck configuration
- Legacy `data/outputs/` automatically migrated to `results/`
- ByteTrack config: `custom_bytetrack.yaml`