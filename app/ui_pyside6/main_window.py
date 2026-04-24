# -*- coding: utf-8 -*-
"""Main window for PySide6 UI."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QStatusBar, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QThreadPool

from .widgets import HeaderWidget, UploadPanel, ResultPanel, ProgressDialog
from .workers import VideoProcessorWorker
from .state import app_state
from .theme import get_theme_manager


class MainWindow(QMainWindow):
    """Main application window integrating all UI components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CCTV Footage Analyzer")
        self.setMinimumSize(1000, 600)
        
        self._thread_pool = QThreadPool()
        self._current_worker = None
        self._progress_dialog = None
        
        self._setup_ui()
        self._connect_signals()
        self._apply_theme()
    
    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_widget.setLayoutDirection(Qt.RightToLeft)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.header = HeaderWidget(self)
        main_layout.addWidget(self.header)
        
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setHandleWidth(1)
        content_splitter.setChildrenCollapsible(False)
        
        self.upload_panel = UploadPanel(self)
        content_splitter.addWidget(self.upload_panel)
        
        self.result_panel = ResultPanel(self)
        content_splitter.addWidget(self.result_panel)
        
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        content_splitter.setSizes([400, 600])
        content_splitter.setMinimumHeight(400)
        
        main_layout.addWidget(content_splitter)
        
        self.status_bar = QStatusBar(self)
        self.status_label = QLabel("جاهز", self)
        self.status_bar.addWidget(self.status_label, 1)
        self.setStatusBar(self.status_bar)
    
    def _connect_signals(self):
        self.header.theme_toggle_requested.connect(self._on_theme_toggle)
        self.header.clear_cache_requested.connect(self._on_clear_cache)
        
        self.upload_panel.process_btn.clicked.connect(self._on_process_request)
        
        app_state.processing_started.connect(self._on_processing_started)
        app_state.processing_finished.connect(self._on_processing_finished)
        app_state.error_occurred.connect(self._on_error)
    
    @Slot()
    def _on_theme_toggle(self):
        theme_manager = get_theme_manager()
        theme_manager.toggle_theme()
    
    @Slot()
    def _on_clear_cache(self):
        self.result_panel.clear()
        self.upload_panel.clear()
        self.status_label.setText("تم مسح ذاكرة التخزين المؤقتة")
        QMessageBox.information(self, "تم", "تم مسح ذاكرة التخزين المؤقتة (ملفات قيد الاستخدام تخطي)")
    
    @Slot()
    def _on_process_request(self):
        video_path = self.upload_panel._current_file
        if not video_path:
            return
        
        self._start_processing(video_path)
    
    def _start_processing(self, video_path: str):
        app_state.is_processing = True
        
        self._progress_dialog = ProgressDialog(self)
        self._progress_dialog.cancelled.connect(self._on_cancel_processing)
        self._progress_dialog.show_with_theme()
        
        self._current_worker = VideoProcessorWorker(video_path)
        self._current_worker.signals.progress.connect(
            self._on_progress
        )
        self._current_worker.signals.result.connect(
            self._on_result
        )
        self._current_worker.signals.error.connect(
            self._on_worker_error
        )
        
        self._thread_pool.start(self._current_worker)
        
        self.status_label.setText("جاري المعالجة...")
        self.upload_panel.set_processing(True)
    
    @Slot(str, int)
    def _on_progress(self, message: str, progress: int):
        print(f"[DEBUG] Progress received: {progress}%")
        if self._progress_dialog:
            self._progress_dialog.update_progress(message, progress)
    
    @Slot(dict)
    def _on_result(self, result: dict):
        print(f"[DEBUG] _on_result called with: {result}")
        try:
            if self._progress_dialog:
                self._progress_dialog.close_with_theme()
            
            print(f"[DEBUG] After close dialog")
            app_state.is_processing = False
            app_state.result = result
            self._current_worker = None
            
            print(f"[DEBUG] Setting status")
            status_msg = "اكتملت المعالجة"
            if result and result.get("cached"):
                status_msg = "تم تحميل النتيجة من ذاكرة التخزين المؤقتة"
            
            self.status_label.setText(status_msg)
            self.upload_panel.set_processing(False)
            
            print(f"[DEBUG] Calling result_panel.set_result")
            if result:
                self.result_panel.set_result(result)
            print(f"[DEBUG] _on_result complete")
        except Exception as e:
            print(f"[DEBUG] Error in _on_result: {e}")
            import traceback
            traceback.print_exc()
            app_state.is_processing = False
            self._current_worker = None
    
    @Slot(str)
    def _on_worker_error(self, error: str):
        try:
            if self._progress_dialog:
                self._progress_dialog.close()
            
            app_state.is_processing = False
            self._current_worker = None
            
            self.status_label.setText("فشلت المعالجة")
            self.upload_panel.set_processing(False)
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("خطأ")
            msg_box.setText(f"حدث خطأ أثناء المعالجة:\n{error}")
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setLayoutDirection(Qt.RightToLeft)
            msg_box.exec()
        except Exception as e:
            print(f"[DEBUG] Error in _on_worker_error: {e}")
    
    @Slot()
    def _on_cancel_processing(self):
        if self._current_worker:
            self._current_worker.cancel()
            self._current_worker = None
        
        app_state.is_processing = False
        self.upload_panel.set_processing(False)
        self.status_label.setText("Processing cancelled")
    
    @Slot()
    def _on_processing_started(self):
        pass
    
    @Slot(dict)
    def _on_processing_finished(self, result: dict):
        self.result_panel.set_result(result)
    
    @Slot(str)
    def _on_error(self, error: str):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("خطأ")
        msg_box.setText(error)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.setLayoutDirection(Qt.RightToLeft)
        msg_box.exec()
    
    def _apply_theme(self):
        theme_manager = get_theme_manager()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        self.setStyleSheet(theme_manager.get_stylesheet())
        self.header.update_theme_icon(True)
    
    @Slot(str)
    def _on_theme_changed(self, theme: str):
        theme_manager = get_theme_manager()
        self.setStyleSheet(theme_manager.get_stylesheet())
        self.header.update_theme_icon(theme == "dark")
    
    def closeEvent(self, event):
        if self._current_worker:
            self._current_worker.cancel()
        
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog.deleteLater()
        
        super().closeEvent(event)