## Plan: Refactor CCTV-Footage-Summarization with PySide6, HuggingFace Hub, and MVC Bridge

TL;DR: Preserve the existing repository structure while enforcing a clean MVC-style bridge between `app/` and `core/`, adding progress-based HuggingFace model download, runtime persistence for logs/history/settings, and export-detected video support.

**Steps**
1. Preserve repository structure.
   - Keep `app/`, `core/`, `data/`, `assets/`, `results/`, and root files.
   - Treat `core/` as the processing model layer and `app/` as the UI/controller layer.
   - Use `app/state/application_state.py` as the shared event bus.

2. Enforce API bridge and verbose diagnostics.
   - Core APIs expose `progress_callback` for UI integration.
   - `VideoProcessorWorker` relays `progress`, `result`, and `error` signals.
   - `ProgressDialog` translates core status messages into UI updates.
   - Add `app/dialogs/dialog_factory.py` for common dialogs.

3. Centralize persistence.
   - Keep JSON storage files in `data/`: `runtime_logs.json`, `history.json`, `settings.json`, `summary_cache.json`.
   - Ensure settings can be saved/restored and history can be reviewed, deleted, or cleared.
   - Keep log pruning via `core/utils/cleanup.py`.

4. Add HuggingFace model download.
   - Use `core/utils/model_download.py` with `ensure_yolo_model()` as the download helper.
   - Add `yolo_model_repo`, `yolo_model_filename`, and `yolo_model_path` to `core/config.py`.
   - Update `core/object_detection.py` and `core/tracking.py` to automatically download missing models.
   - Route download progress through the shared progress dialog.

5. Match config semantics.
   - Standardize `percent_changed_thresh` across config and frame selection as a ratio.
   - Preserve `cuda_alloc_conf` and `max_memory_fraction` because they are used in GPU settings.

6. Export detected video support.
   - Enable `ResultPanel.export_detected_btn` when selected frames exist.
   - Launch `VideoProcessorWorker(task_type="export_detected")` on button click.
   - Copy the generated detected video to a user-specified location and launch it.

7. Verify.
   - Activate the repository venv and install requirements.
   - Launch `python -m app.main`.
   - Run a summarization job and verify outputs under `results/{video-name}/`.
   - Confirm `ProgressDialog` displays core progress and model download status.
   - Confirm settings/history persistence and system info display.

**Relevant files**
- `requirements.txt`
- `core/config.py`
- `core/utils/model_download.py`
- `core/object_detection.py`
- `core/tracking.py`
- `core/summarizer.py`
- `app/main.py`
- `app/main_window.py`
- `app/workers/video_processor.py`
- `app/widgets/result_panel.py`
- `app/widgets/progress_dialog.py`
- `app/widgets/system_info_panel.py`
- `app/widgets/settings_panel.py`
- `app/widgets/history_panel.py`
- `app/state/application_state.py`
- `app/dialogs/dialog_factory.py`
