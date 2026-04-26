from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import api
from ..theme import apply_card_shadow


VIDEO_FILTER = "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"


class UploadPanel(QFrame):
    video_selected = Signal(str)
    process_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setLayoutDirection(Qt.RightToLeft)
        apply_card_shadow(self)
        self._video_path: Optional[str] = None
        self._setup_ui()
        self._set_empty()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(repo_root, "assets", "logo_128.svg")
        if os.path.exists(logo_path):
            from PySide6.QtSvgWidgets import QSvgWidget
            icon = QSvgWidget(logo_path, header)
            icon.setFixedSize(24, 24)
        else:
            icon = QLabel("📥", header)
            icon.setStyleSheet("font-size: 18px;")
        title = QLabel("رفع الفيديو", header)
        title.setStyleSheet("font-size: 14px; font-weight: bold;")

        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.select_btn = QPushButton("اختيار فيديو", self)
        self.select_btn.setObjectName("primary_btn")
        self.select_btn.clicked.connect(self._pick_video)

        layout.addWidget(header)
        layout.addWidget(self.select_btn)

        info_box = QWidget(self)
        form = QFormLayout(info_box)
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignTop)

        self.name_val = QLabel("-", info_box)
        self.size_val = QLabel("-", info_box)
        self.duration_val = QLabel("-", info_box)
        self.fps_val = QLabel("-", info_box)
        self.frames_val = QLabel("-", info_box)
        self.hash_val = QLabel("-", info_box)
        self.hash_val.setTextInteractionFlags(Qt.TextSelectableByMouse)

        form.addRow("اسم الملف:", self.name_val)
        form.addRow("الحجم:", self.size_val)
        form.addRow("المدة:", self.duration_val)
        form.addRow("FPS:", self.fps_val)
        form.addRow("عدد الإطارات:", self.frames_val)
        form.addRow("SHA-256:", self.hash_val)

        layout.addWidget(info_box)
        layout.addStretch()

        self.process_btn = QPushButton("بدء التلخيص", self)
        self.process_btn.setObjectName("primary_btn")
        self.process_btn.clicked.connect(self._emit_process)
        layout.addWidget(self.process_btn)

    def _pick_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "اختر الفيديو", "", VIDEO_FILTER)
        if not path:
            return
        self.set_video(path)

    def set_video(self, path: str) -> None:
        if not os.path.exists(path):
            self._set_empty()
            return

        self._video_path = path
        info = api.get_video_info(path)

        self.name_val.setText(info["name"])
        self.size_val.setText(api.format_file_size(info["size_bytes"]))
        dur = info.get("duration_sec")
        self.duration_val.setText(f"{dur:.2f} ثانية" if isinstance(dur, (int, float)) else "-")
        self.fps_val.setText(f"{info.get('fps', 0.0):.2f}")
        self.frames_val.setText(str(info.get("frame_count", "-")))
        try:
            self.hash_val.setText(api.compute_sha256(path)[:16])
        except Exception:
            self.hash_val.setText("-")

        self.process_btn.setEnabled(True)
        self.video_selected.emit(path)

    def current_video(self) -> Optional[str]:
        return self._video_path

    def set_processing(self, processing: bool) -> None:
        self.select_btn.setEnabled(not processing)
        self.process_btn.setEnabled((not processing) and bool(self._video_path))

    def clear(self) -> None:
        self._set_empty()
        self.video_selected.emit("")

    def _set_empty(self) -> None:
        self._video_path = None
        self.name_val.setText("-")
        self.size_val.setText("-")
        self.duration_val.setText("-")
        self.fps_val.setText("-")
        self.frames_val.setText("-")
        self.hash_val.setText("-")
        self.process_btn.setEnabled(False)

    def _emit_process(self) -> None:
        if self._video_path:
            self.process_requested.emit(self._video_path)
