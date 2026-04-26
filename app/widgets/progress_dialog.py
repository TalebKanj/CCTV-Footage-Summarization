# app/widgets/progress_dialog.py
from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit
from PySide6.QtCore import Qt

from ..theme import get_theme_manager

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("جاري معالجة الفيديو")
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.resize(520, 380)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout()

        self.status_label = QLabel("جاري التهيئة...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(160)
        self.log_box.setPlaceholderText("سجل التشخيص سيظهر هنا…")
        layout.addWidget(self.log_box, 1)

        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.setObjectName("danger_btn")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.setStyleSheet(get_theme_manager().get_stylesheet())

    def update_progress(self, message, percent):
        self.status_label.setText(message)
        self.progress_bar.setValue(percent)
        ts = datetime.now().strftime("%H:%M:%S")
        try:
            self.log_box.append(f"[{ts}] {message} ({int(percent)}%)")
        except Exception:
            pass
