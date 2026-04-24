"""Video processor worker for PySide6 background processing."""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PySide6.QtCore import QRunnable, Signal, QObject


class WorkerSignals(QObject):
    progress = Signal(str, int)
    result = Signal(dict)
    error = Signal(str)


class VideoProcessorWorker(QRunnable):
    """QRunnable worker for video summarization processing."""
    
    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = video_path
        self.signals = WorkerSignals()
        self._is_cancelled = False
    
    def cancel(self):
        self._is_cancelled = True
    
    def run(self):
        try:
            if self._is_cancelled:
                return
            
            print(f"[DEBUG] Starting processing: {self.video_path}")
            self.signals.progress.emit("Loading video...", 2)
            
            from core.summarizer import summarize_video
            
            if self._is_cancelled:
                return
            
            print(f"[DEBUG] Calling summarize_video for: {self.video_path}")
            result = summarize_video(
                self.video_path,
                progress_callback=self._on_progress
            )
            
            print(f"[DEBUG] Processing complete, result keys: {result.keys()}")
            
            if self._is_cancelled:
                return
            
            self.signals.result.emit(result)
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
            self.signals.error.emit(error_msg)
    
    def _on_progress(self, message: str, progress: int):
        if not self._is_cancelled:
            progress_int = int(progress)
            print(f"[DEBUG] Progress emit: {progress_int}%")
            self.signals.progress.emit(message, progress_int)