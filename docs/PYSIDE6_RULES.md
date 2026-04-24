# PySide6 Migration Rules
# Comprehensive implementation guidelines for CCTV Footage Summarization PySide6 UI

## Core Principles

### Thread Safety
1. **NEVER update UI from worker threads** - use signals with Qt.QueuedConnection
2. **ALWAYS use deleteLater()** instead of `del` for widget cleanup
3. **ALWAYS use proper parent assignment** - every widget needs a parent
4. **NEVER use QDialog.exec_()** - use open() with signals for non-blocking dialogs
5. **ALWAYS wrap blocking operations in QRunnable** - never block main thread
6. **Use Qt.QueuedConnection** for all worker signal connections
7. **Always provide parent to widgets**: `QLabel("text", self)`
8. **Disconnect signals before widget destruction**

### Signal/Slot Decorators
```python
from PySide6.QtCore import Signal, Slot, QObject

class WorkerSignals(QObject):
    progress = Signal(str, int)  # message, percentage
    result = Signal(dict)       # result dictionary
    error = Signal(str)         # error message
```

### QRunnable Pattern
```python
class VideoProcessorRunnable(QRunnable):
    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = video_path
        self.signals = WorkerSignals()
    
    def run(self):
        try:
            # Processing code here
            self.signals.progress.emit("Loading video", 10)
            result = summarize_video(self.video_path, self._progress_callback)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
    
    def _progress_callback(self, msg: str, progress: int):
        self.signals.progress.emit(msg, progress)
```

## Theme System

### Syrian-Inspired Colors
| Element | Dark Mode | Light Mode |
|---------|-----------|------------|
| Primary (Red) | #CE1126 | #CE1126 |
| Gold | #B9A779 | #B9A779 |
| Background (Dark) | #002623 | #f8f9fa |
| Surface (Dark) | #1a2332 | #f1f3f5 |
| Text Primary | #E8E6E3 | #1a1d21 |
| Border | #988561 | #988561 |

### Style Sheet Template
```python
DARK_STYLESHEET = """
QMainWindow {
    background-color: #002623;
}
QPushButton {
    background: linear-gradient(135deg, #CE1126 0%, #B9A779 100%);
    color: #f8f9fa;
    border: none;
    border-radius: 7px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background: #CE1126;
}
QProgressBar {
    border: 1px solid #988561;
    border-radius: 5px;
    text-align: center;
    background-color: #1a2332;
}
QProgressBar::chunk {
    background: linear-gradient(90deg, #CE1126 0%, #B9A779 100%);
}
"""
```

## Application State

### Singleton Pattern
```python
class ApplicationState(QObject):
    _instance = None
    
    videoSelected = Signal(str)
    processingStarted = Signal()
    processingFinished = Signal(dict)
    themeChanged = Signal(str)
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

## File Utils

### Hash Computation
```python
def compute_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(8192), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
```

### Video File Filter
```python
VIDEO_FILTER = "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*.*)"
```

## Widget Hierarchy

```
MainWindow
+-- HeaderWidget (sticky top)
+-- QSplitter (horizontal)
¦   +-- UploadPanel (left side, ~400px)
¦   +-- ResultPanel (right side, expanding)
+-- StatusBar (bottom)
+-- ProgressDialog (modal, non-blocking)
```

## Widget Specifications

### HeaderWidget
- Height: 60px
- Contains: Logo (SVG or placeholder), Title, Theme toggle button
- Border bottom: 1px solid #988561

### UploadPanel
- Fixed width: 400px
- Contains: Drop zone, File info grid, Process button
- Drop zone: Dashed border, accepts video files

### ResultPanel
- Expanding width
- Contains: Video player, Download buttons, Empty state
- Shows result when processing complete

### ProgressDialog
- Non-modal with open() pattern
- Shows current step and progress bar
- Cancel button available
- Signals: cancelled

## Processing Pipeline

### Steps (matching core/summarizer.py)
1. Loading video (2-5%)
2. Frame selection (5-30%)
3. Keyframe extraction (30-55%)
4. Segment building (55-70%)
5. Video reconstruction (70-90%)
6. Finalizing output (90-100%)

## Dependencies

Required packages:
- PySide6
- opencv-python
- ultralytics
- numpy

## Entry Point

```bash
python -m app.ui_pyside6.main
# or
python app/ui_pyside6/main.py
```

## Testing

Test after implementation:
```bash
cd project_root
python -m app.ui_pyside6.main
```

Verify:
1. Window opens without errors
2. Theme toggle works
3. Video drop/select works
4. Progress updates during processing
5. Results display after completion
