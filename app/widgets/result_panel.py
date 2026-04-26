from __future__ import annotations

import os
import subprocess
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .video_comparison_panel import VideoComparisonPanel
from ..theme import apply_card_shadow


class ResultPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setLayoutDirection(Qt.RightToLeft)
        apply_card_shadow(self)
        self._input_path: Optional[str] = None
        self._result: Optional[dict] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        icon = QLabel("✅", header)
        icon.setStyleSheet("font-size: 18px;")
        title = QLabel("النتائج", header)
        title.setStyleSheet("font-size: 14px; font-weight: bold;")

        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.open_folder_btn = QPushButton("فتح المجلد", self)
        self.open_folder_btn.clicked.connect(self._open_output_dir)
        self.open_folder_btn.setEnabled(False)
        header_layout.addWidget(self.open_folder_btn)

        layout.addWidget(header)

        self.summary_label = QLabel("لا توجد نتائج بعد.", self)
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        layout.addWidget(self.summary_label)

        self.comparison = VideoComparisonPanel(self)
        layout.addWidget(self.comparison, 1)

    def set_input_video(self, path: Optional[str]) -> None:
        self._input_path = path if path and os.path.exists(path) else None
        self._refresh_players()

    def set_result(self, result: dict) -> None:
        self._result = result or None
        if not result:
            self.summary_label.setText("لا توجد نتائج.")
            self.open_folder_btn.setEnabled(False)
            self._refresh_players()
            return

        out_dir = result.get("output_dir") or "—"
        reduced = result.get("frames_reduced_pct")
        segs = result.get("segments_count")
        cached = result.get("cached")
        bits = [f"المخرجات: {out_dir}"]
        if reduced is not None:
            bits.append(f"تقليل الإطارات: {reduced}%")
        if segs is not None:
            bits.append(f"عدد المقاطع: {segs}")
        if cached:
            bits.append("ملاحظة: تم تحميل النتيجة من الكاش")
        self.summary_label.setText(" | ".join(bits))
        self.open_folder_btn.setEnabled(bool(result.get("output_dir")))
        self._refresh_players()

    def _refresh_players(self) -> None:
        summary_path = None
        if self._result:
            summary_path = self._result.get("segments_video")
        self.comparison.set_summary(summary_path, self._result)

    def _open_output_dir(self) -> None:
        if not self._result:
            return
        out_dir = self._result.get("output_dir")
        if not out_dir or not os.path.exists(out_dir):
            return
        try:
            os.startfile(out_dir)  # type: ignore[attr-defined]
        except Exception:
            subprocess.Popen(["explorer", out_dir])
