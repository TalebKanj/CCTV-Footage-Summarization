# AGENTS.md

## Running

```bash
python -m app.main            # Desktop UI (recommended)
```

## Setup

1. `data/inputs/test.mp4` - Place input video
2. `models/yolov8n.pt` - Download from https://docs.ultralytics.com/
3. `pip install -r requirements.txt`

Target: Python 3.13, PyTorch 2.9.0, CUDA 13

## Architecture

| Directory | Purpose |
|-----------|---------|
| `core/` | ML pipeline (MOG2, YOLOv8, summarizer, tracking) |
| `app/` | Desktop UI (Arabic-first, Syrian theme) |
| `data/` | JSON storage (cache, history, settings, logs) |

Configuration: Edit `core/config.py` or set environment variables.

## PySide6 UI ↔ Core Bridge (MVC-like)

```
┌─────────────────────────────────────────────────────────────┐
│  app/                                            │
│  ├── main_window.py    # Controller: orchestrates widgets   │
│  ├── workers/video_processor.py  # Background worker (QRunnable)│
│  │   └── calls core.summarize_video()                     │
│  ├── widgets/           # View: header, upload, result panels │
│  └── state/application_state.py  # Model: Qt Signal state   │
└─────────────────────────────────────────────────────────────┘
                           ↓ calls
┌─────────────────────────────────────────────────────────────┐
│  core/summarizer.py                                        │
│  └── summarize_video(input_path, config, progress_callback) │
│      # Main API: coordinates frame_selection → segments → video│
└─────────────────────────────────────────────────────────────┘
```

### Key Bridge Points

- **Entry**: `core/summarize_video(input_path, config, progress_callback)` at `core/summarizer.py:169`
- **Progress**: UI receives updates via `progress_callback(message, percent)` - Arabic messages
- **Result**: Returns dict with `frames_video`, `segments_video`, `output_dir`, `cached`, `checksum`
- **Worker**: `VideoProcessorWorker` runs in `QThreadPool`, emits signals: `progress`, `result`, `error`

### State Management

- Global state via `app.state.app_state` (Qt Signal-based singleton)
- Properties: `is_processing`, `result`, `error`

## Data Layer (Database System)

JSON-based storage in `data/` directory:

| File | Purpose |
|------|---------|
| `data/summary_cache.json` | Video checksum cache (SHA-256 keys) |
| `data/history.json` | Video summarization history |
| `data/settings.json` | User preferences |
| `data/runtime_logs.json` | Runtime logs (30-day retention) |

### History Format (`data/history.json`)

```json
{
  "videos": [
    {
      "id": "uuid",
      "video_name": "test.mp4",
      "checksum": "sha256",
      "timestamp": "ISO8601",
      "input_path": "path",
      "output_dir": "path",
      "config_snapshot": {...},
      "duration_sec": 120.5,
      "frames_reduced_pct": 80.5,
      "segments_count": 12
    }
  ]
}
```

### Log Retention

- Runtime logs auto-expire after 30 days
- Implement via `core/utils/cleanup.py`: check timestamp on load, prune expired entries

## UI Layout

Bottom tab structure in `main_window.py`:
- Tab 0: Results (default)
- Tab 1: Settings
- Tab 2: System Info / CUDA
- Tab 3: History

### Settings Tab

Fields: `pixel_diff_thresh`, `percent_changed_thresh`, `summary_fps`, `merge_gap_sec`, `pre_event_sec`, `post_event_sec`, `yolo_confidence`

Controls:
- Save Settings → writes to `data/settings.json`
- Restore Defaults → resets to `core/config.py` defaults
- Live preview of changed values

### System Info Tab

Display:
- OS, CPU, RAM (via `platform` + `psutil`)
- CUDA available + version (via `torch.cuda.is_available()`, `torch.version.cuda`)
- GPU name, VRAM total/free/used (via `torch.cuda.get_device_properties`, `torch.cuda.memory_stats`)
- CUDA benchmark button

CUDA Benchmark: Process first 5 seconds of uploaded video clip (non-blocking in worker thread)

### History Tab

Display: Sortable table (video name, date, duration, frames reduced %, segments)

Controls:
- Clear History → removes all entries from `data/history.json`
- Delete Entry → removes selected row

## Common Dialogs System

`app/dialogs/dialog_factory.py`:

| Method | Purpose |
|--------|---------|
| `show_info(parent, title, message)` | Information message |
| `show_warning(parent, title, message)` | Warning message |
| `show_error(parent, title, message)` | Error message |
| `show_confirm(parent, title, message)` → bool | Yes/No confirmation |
| `show_file_open(parent, filter)` → str | File picker |
| `show_file_save(parent, filter, default)` → str | Save-as picker |

Initialize on app startup (lazy singletons). All dialogs: `LayoutDirection = RightToLeft`, centered on parent.

## Progress Dialog Callback

`ProgressDialog` acts as bridge for `progress_callback`:

- Receives `(message: str, percent: int)` from core pipeline
- Displays Arabic status message in progress dialog
- Stores log messages in internal history for display
- Cancel button emits `cancelled` signal → `VideoProcessorWorker.cancel()`

## Key Config (`core/config.py`)

- `pixel_diff_thresh`: 15 (MOG2 varThreshold)
- `percent_changed_thresh`: 0.15
- `summary_fps`: 12
- `yolo_confidence`: 0.3
- `allowed_classes`: ["person", "car"]
- `merge_gap_sec`: 2.0, `pre_event_sec`: 2.0, `post_event_sec`: 4.0
- `mog2_history`: 500, `mog2_var_threshold`: 15, `buffer_duration_sec`: 1.5

## Output

`results/{video-name}/`:
- `selected_frames/` - Motion keyframes
- `summaries/summary_segments.mp4` - Main output
- `detected_frames/` - YOLO annotated
- `logs/segments.json` - Metadata

## Cache

`data/summary_cache.json` - SHA-256 based, survives file renames.

## Diagnostic Output

Debug output uses `[DEBUG]` and `[ERROR]` prefixes:

| File | Purpose |
|------|---------|
| `app/workers/video_processor.py` | Worker lifecycle: start, progress, result, errors |
| `app/main_window.py` | UI callbacks: progress, result, error slots |
| `app/state/application_state.py` | State changes |

### Debug Patterns

```python
print(f"[DEBUG] Starting processing: {video_path}")
print(f"[DEBUG] Progress emit: {progress_int}%")
print(f"[DEBUG] _on_result called with: {result}")
print(f"[ERROR] {error_msg}")
```

## Known Issues

- Streamlit UI deprecated - use PySide6 exclusively
- MOG2 shadows disabled for CCTV stability