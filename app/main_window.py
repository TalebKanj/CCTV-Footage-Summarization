from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Slot, QThreadPool, QTimer
from PySide6.QtWidgets import QFrame, QMainWindow, QScrollArea, QSplitter, QTabWidget, QVBoxLayout, QWidget

import api

from .dialogs.dialog_factory import show_error, show_file_open
from .state.application_state import app_state
from .theme import get_theme_manager
from .widgets.history_panel import HistoryPanel
from .widgets.progress_dialog import ProgressDialog
from .widgets.result_panel import ResultPanel
from .widgets.settings_panel import SettingsPanel
from .widgets.system_info_panel import SystemInfoPanel
from .widgets.upload_panel import UploadPanel
from .workers.video_processor import VideoProcessorWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تحليل لقطات المراقبة")
        self.setMinimumSize(1200, 720)
        self.setLayoutDirection(Qt.RightToLeft)

        self._thread_pool = QThreadPool.globalInstance()
        self._current_worker: Optional[VideoProcessorWorker] = None
        self._progress_dialog: Optional[ProgressDialog] = None

        self._setup_ui()
        self._connect_signals()
        self._apply_theme()

    def _setup_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # All panels as tabs (dashboard included) to prevent underlay/overstack issues.
        self.tabs = QTabWidget(central)
        self.tabs.setDocumentMode(True)
        self.tabs.setLayoutDirection(Qt.RightToLeft)

        dashboard = QWidget(self.tabs)
        dash_layout = QVBoxLayout(dashboard)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        dash_layout.setSpacing(10)

        splitter = QSplitter(Qt.Horizontal, dashboard)
        splitter.setChildrenCollapsible(False)

        self.upload_panel = UploadPanel(splitter)
        self.result_panel = ResultPanel(splitter)

        splitter.addWidget(self.upload_panel)
        splitter.addWidget(self.result_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([340, 860])

        dash_layout.addWidget(splitter, 1)

        settings_scroll = QScrollArea(self.tabs)
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.NoFrame)
        self.settings_panel = SettingsPanel(settings_scroll)
        settings_scroll.setWidget(self.settings_panel)

        self.history_panel = HistoryPanel(self.tabs)
        self.system_panel = SystemInfoPanel(self.tabs)

        self.tabs.addTab(dashboard, "الرئيسية")
        self.tabs.addTab(settings_scroll, "التحكم")
        self.tabs.addTab(self.history_panel, "السجل")
        self.tabs.addTab(self.system_panel, "معلومات النظام")

        root.addWidget(self.tabs, 1)

    def _connect_signals(self) -> None:
        theme_manager = get_theme_manager()
        theme_manager.theme_changed.connect(self._on_theme_changed)

        self.upload_panel.video_selected.connect(self._on_video_selected)
        self.upload_panel.process_requested.connect(self._on_process_request)

        app_state.processing_changed.connect(self._on_processing_changed)
        app_state.error_changed.connect(self._on_error)
        app_state.result_changed.connect(self._on_result_state_changed)

    def _apply_theme(self) -> None:
        self._on_theme_changed(get_theme_manager().current_theme)

    @Slot(str)
    def _on_theme_changed(self, theme: str) -> None:
        self.setStyleSheet(get_theme_manager().get_stylesheet())

    @Slot(str)
    def _on_video_selected(self, path: str) -> None:
        self.result_panel.set_input_video(path or None)
        try:
            self.system_panel.set_video_path(path or None)
        except Exception:
            pass

    @Slot(str)
    def _on_process_request(self, video_path: str) -> None:
        if not video_path:
            return
        self._start_processing(video_path)

    def _start_processing(self, video_path: str) -> None:
        if self._current_worker is not None:
            return

        config = api.load_settings()
        config.update(self.settings_panel.get_settings())
        try:
            print(f"[DEBUG] UI requested processing: {video_path}")
            redacted = dict(config)
            if redacted.get("hf_token"):
                redacted["hf_token"] = "***"
            print(f"[DEBUG] UI merged config: {redacted}")
        except Exception:
            pass

        self._progress_dialog = ProgressDialog(self)
        self._progress_dialog.show()

        worker = VideoProcessorWorker(video_path, config)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.result.connect(lambda res: self._on_worker_result(video_path, config, res))
        worker.signals.error.connect(self._on_worker_error)
        worker.signals.finished.connect(self._on_worker_finished)

        if self._progress_dialog:
            self._progress_dialog.cancel_button.clicked.connect(worker.cancel)

        self._current_worker = worker
        app_state.is_processing = True
        self.upload_panel.set_processing(True)
        self._thread_pool.start(worker)

    @Slot(str, int)
    def _on_progress(self, message: str, percent: int) -> None:
        if self._progress_dialog:
            self._progress_dialog.update_progress(message, percent)

    def _on_worker_result(self, video_path: str, config: dict, result: dict) -> None:
        try:
            print(f"[DEBUG] _on_worker_result called for: {video_path}")
            print(f"[DEBUG] Result summary: segments_video={result.get('segments_video')}, cached={result.get('cached')}")
        except Exception:
            pass
        app_state.result = result
        try:
            api.add_history_entry(video_path, result, config_snapshot=config)
            self.history_panel.reload()
        except Exception:
            pass

    @Slot(str)
    def _on_worker_error(self, error: str) -> None:
        try:
            print(f"[ERROR] Worker error received: {error}")
        except Exception:
            pass
        app_state.error = error

    @Slot()
    def _on_worker_finished(self) -> None:
        app_state.is_processing = False
        self.upload_panel.set_processing(False)
        self._current_worker = None
        if self._progress_dialog:
            self._progress_dialog.accept()
            self._progress_dialog = None

    @Slot(bool)
    def _on_processing_changed(self, processing: bool) -> None:
        self.upload_panel.set_processing(processing)

    @Slot(str)
    def _on_error(self, error: str) -> None:
        if not error:
            return
        show_error(self, "خطأ", error)

    @Slot(dict)
    def _on_result_state_changed(self, result: dict) -> None:
        self.result_panel.set_result(result)
