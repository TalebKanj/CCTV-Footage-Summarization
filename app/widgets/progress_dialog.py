# -*- coding: utf-8 -*-
"""Progress dialog widget for PySide6 UI."""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QTextEdit
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QTextCursor, QColor

from ..theme import get_theme_manager
from ..fonts import get_app_font


class ProgressDialog(QDialog):
    """Non-blocking progress dialog for video processing."""

    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("جاري المعالجة...")
        self.setModal(False)
        self.setMinimumSize(450, 280)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.icon_label = QLabel("⚙", self)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 32px;")

        self.step_label = QLabel("جاري تهيئة معالجة الفيديو...", self)
        self.step_label.setAlignment(Qt.AlignCenter)
        self.step_label.setFont(get_app_font("Bold", 13))
        self.step_label.setWordWrap(True)
        self.step_label.setStyleSheet("padding: 4px;")

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.percent_label = QLabel("٪0", self)
        self.percent_label.setAlignment(Qt.AlignCenter)
        self.percent_label.setFont(get_app_font("Regular", 11))
        self.percent_label.setStyleSheet("color: #B8B8B8;")

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(80)
        self.log_text.setFont(get_app_font("Regular", 9))
        self.log_text.setLayoutDirection(Qt.RightToLeft)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("إلغاء", self)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._on_cancel)

        button_layout.addWidget(self.cancel_btn)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.step_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.percent_label)
        layout.addWidget(self.log_text)
        layout.addLayout(button_layout)
    
    @Slot(str, int)
    def update_progress(self, message: str, percent: int):
        self.step_label.setText(message)
        self.percent_label.setText(f"٪{percent}")
        self.progress_bar.setValue(percent)
        self.progress_bar.repaint()
        self._append_log(message)

    @Slot(str)
    def log_message(self, message: str):
        self._append_log(message)

    def _append_log(self, message: str):
        self.log_text.append(f"• {message}")
        self.log_text.moveCursor(QTextCursor.End)

    def clear_logs(self):
        self.log_text.clear()
    
    def _on_cancel(self):
        self.cancelled.emit()
        self.close()
    
    def show_with_theme(self):
        theme_manager = get_theme_manager()
        self.setStyleSheet(theme_manager.get_stylesheet())
        self.log_text.setTextColor(QColor("#B9A779"))
        self.open()
    
    def close_with_theme(self):
        self.progress_bar.setValue(100)
        self.step_label.setText("اكتملت المعالجة!")
        self.percent_label.setText("٪100")
        self.icon_label.setText("✓")
        self._append_log("اكتملت المعالجة بنجاح!")
        self.cancel_btn.setText("إغلاق")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.close)
        
        QTimer.singleShot(1500, self.close)
    
    def reset(self):
        self.progress_bar.setValue(0)
        self.step_label.setText("جاري تهيئة معالجة الفيديو...")
        self.percent_label.setText("٪0")
        self.icon_label.setText("⚙")
        self.cancel_btn.setText("إلغاء")
        self.clear_logs()