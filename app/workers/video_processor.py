from __future__ import annotations

import traceback

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

import api


class VideoProcessorSignals(QObject):
    progress = Signal(str, int)  # message, percent
    result = Signal(dict)
    error = Signal(str)
    finished = Signal()


def _format_exception_message(exc: BaseException) -> str:
    msg = str(exc).strip()
    if isinstance(exc, InterruptedError):
        return "تم إلغاء العملية."
    if "Weights only load failed" in msg or "weights_only" in msg:
        return (
            "تعذر تحميل أوزان YOLO بسبب قيود PyTorch (weights_only). "
            "تم تطبيق إصلاح تلقائي، أعد المحاولة. "
            "إذا استمرت المشكلة: حدّث Ultralytics أو استخدم ملف أوزان رسمي موثوق."
        )
    if not msg:
        return exc.__class__.__name__
    return msg


class VideoProcessorWorker(QRunnable):
    """Background worker for video summarization.

    Runs in a `QThreadPool` and communicates back via Qt signals.
    """

    def __init__(self, video_path: str, config: dict):
        super().__init__()
        self.video_path = video_path
        self.config = config
        self.signals = VideoProcessorSignals()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @Slot()
    def run(self) -> None:
        try:
            print(f"[DEBUG] Starting processing: {self.video_path}")
            print(f"[DEBUG] Config keys: {sorted(list(self.config.keys()))}")

            last_percent = {"value": -1}

            def progress_callback(message: str, percent: int) -> None:
                if self._cancelled:
                    raise InterruptedError("Processing cancelled")
                self.signals.progress.emit(message, int(percent))
                try:
                    p = int(percent)
                    if p == 0 or p == 100 or p - last_percent["value"] >= 10:
                        last_percent["value"] = p
                        print(f"[DEBUG] Progress emit: {p}% - {message}")
                except Exception:
                    pass

            result = api.summarize_video(self.video_path, self.config, progress_callback)
            print(f"[DEBUG] Processing result keys: {sorted(list((result or {}).keys()))}")
            self.signals.result.emit(result)
        except Exception as exc:
            # Keep full traceback in console for diagnostics, but show only the exception message in the UI.
            tb = traceback.format_exc()
            print(f"[ERROR] Worker exception:\n{tb}")
            self.signals.error.emit(_format_exception_message(exc))
        finally:
            self.signals.finished.emit()
