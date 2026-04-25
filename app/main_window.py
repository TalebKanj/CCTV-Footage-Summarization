# -*- coding: utf-8 -*-
"""Main window for PySide6 UI."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QStatusBar, QLabel, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt, Slot, QThreadPool, QTimer

from .widgets import HeaderWidget, UploadPanel, ResultPanel, ProgressDialog, SettingsPanel
from .workers import VideoProcessorWorker
from .state import app_state
from .theme import get_theme_manager


class MainWindow(QMainWindow):
    """Main application window integrating all UI components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تحليل لقطات المراقبة")
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
        
        self.tabs = QTabWidget(self)
        self.tabs.setLayoutDirection(Qt.RightToLeft)
        self.tabs.setDocumentMode(True)
        
        self.results_tab = self._create_results_tab()
        self.tabs.addTab(self.results_tab, "النتائج")
        
        self.settings_tab = SettingsPanel(self)
        self.tabs.addTab(self.settings_tab, "الإعدادات")
        
        self.system_tab = self._create_system_tab()
        self.tabs.addTab(self.system_tab, "معلومات النظام")
        
        self.history_tab = self._create_history_tab()
        self.tabs.addTab(self.history_tab, "السجل")
        
        main_layout.addWidget(self.tabs)
        
        self.status_bar = QStatusBar(self)
        self.status_label = QLabel("جاهز", self)
        self.status_label.setObjectName("status_label")
        self.status_bar.addWidget(self.status_label, 1)
        self.setStatusBar(self.status_bar)
    
    def _create_results_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        from .widgets import UploadPanel, ResultPanel
        
        splitter = QWidget(widget)
        splitter_layout = QHBoxLayout(splitter)
        splitter_layout.setContentsMargins(0, 0, 0, 0)
        splitter_layout.setSpacing(0)
        
        self.upload_panel = UploadPanel(splitter)
        self.result_panel = ResultPanel(splitter)
        
        splitter_layout.addWidget(self.upload_panel)
        splitter_layout.addWidget(self.result_panel)
        
        splitter.setMinimumHeight(400)
        layout.addWidget(splitter)
        
        return widget
    
    def _create_system_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        
        title = QLabel("معلومات النظام", widget)
        title.setFont(self.font())
        layout.addWidget(title)
        
        content = QLabel("جاري تحميل المعلومات...", widget)
        layout.addWidget(content)
        
        layout.addStretch()
        return widget
    
    def _create_history_tab(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        
        title = QLabel("سجل المعالجة", widget)
        title.setFont(self.font())
        layout.addWidget(title)
        
        content = QLabel("لا توجد معالجات سابقة.", widget)
        layout.addWidget(content)
        
        layout.addStretch()
        return widget
    
    def font(self):
        from .fonts import get_app_font
        return get_app_font("Bold", 14)
    
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
        QMessageBox.information(self, "تم", "تم مسح ذاكرة التخزين المؤقتة")
    
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
            
            app_state.is_processing = False
            app_state.result = result
            self._current_worker = None
            
            status_msg = "اكتملت المعالجة"
            if result and result.get("cached"):
                status_msg = "تم تحميل النتيجة من ذاكرة التخزين المؤقتة"
            
            self.status_label.setText(status_msg)
            QTimer.singleShot(5000, lambda: self.status_label.setText("جاهز"))
            self.upload_panel.set_processing(False)
            
            if result:
                self.result_panel.set_result(result)
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
        self.status_label.setText("تم الإلغاء")
    
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