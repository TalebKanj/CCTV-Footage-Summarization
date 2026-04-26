from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import api
from ..theme import apply_card_shadow


class HistoryPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setLayoutDirection(Qt.RightToLeft)
        apply_card_shadow(self)
        self._setup_ui()
        self.reload()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        icon = QLabel("🕘", header)
        icon.setStyleSheet("font-size: 18px;")
        title = QLabel("السجل", header)
        title.setStyleSheet("font-size: 14px; font-weight: bold;")

        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.open_btn = QPushButton("فتح", self)
        self.open_btn.clicked.connect(self.open_selected)

        self.delete_btn = QPushButton("حذف", self)
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.clicked.connect(self.delete_selected)

        self.clear_btn = QPushButton("مسح الكل", self)
        self.clear_btn.setObjectName("danger_btn")
        self.clear_btn.clicked.connect(self.clear_all)

        header_layout.addWidget(self.open_btn)
        header_layout.addWidget(self.delete_btn)
        header_layout.addWidget(self.clear_btn)
        layout.addWidget(header)

        self.table = QTableWidget(self)
        self.table.setLayoutDirection(Qt.RightToLeft)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["اسم الفيديو", "التاريخ", "المدة", "تقليل الإطارات %", "عدد المقاطع"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table, 1)

        footer = QLabel("يعرض آخر العمليات. يمكنك فتح مجلد النتائج من زر (فتح).", self)
        footer.setStyleSheet("opacity: 0.8;")
        footer.setWordWrap(True)
        layout.addWidget(footer)

    def reload(self) -> None:
        self.table.setSortingEnabled(False)
        rows = api.list_history()
        self.table.setRowCount(len(rows))
        for i, entry in enumerate(rows):
            self._set_row(i, entry)
        self.table.setSortingEnabled(True)
        # Columns are stretched to fit the panel.

    def _set_row(self, row: int, entry: Dict[str, Any]) -> None:
        entry_id = entry.get("id", "")
        name = str(entry.get("video_name", "—"))
        ts = str(entry.get("timestamp", "—"))
        dur = entry.get("duration_sec")
        red = entry.get("frames_reduced_pct")
        segs = entry.get("segments_count")

        def item(text: str) -> QTableWidgetItem:
            it = QTableWidgetItem(text)
            it.setData(Qt.UserRole, entry_id)
            return it

        self.table.setItem(row, 0, item(name))
        self.table.setItem(row, 1, item(ts))
        self.table.setItem(row, 2, item(f"{dur:.1f}s" if isinstance(dur, (int, float)) else "—"))
        self.table.setItem(row, 3, item(f"{red:.2f}%" if isinstance(red, (int, float)) else "—"))
        self.table.setItem(row, 4, item(str(segs) if segs is not None else "—"))

    def _selected_entry_id(self) -> Optional[str]:
        row = self.table.currentRow()
        if row < 0:
            return None
        it = self.table.item(row, 0)
        if it is None:
            return None
        return it.data(Qt.UserRole)

    def open_selected(self) -> None:
        entry_id = self._selected_entry_id()
        if not entry_id:
            return
        entry = next((e for e in api.list_history() if e.get("id") == entry_id), None)
        if not entry:
            return
        out_dir = entry.get("output_dir")
        if out_dir and os.path.exists(out_dir):
            try:
                os.startfile(out_dir)  # type: ignore[attr-defined]
            except Exception:
                subprocess.Popen(["explorer", out_dir])

    def delete_selected(self) -> None:
        entry_id = self._selected_entry_id()
        if not entry_id:
            return
        api.delete_history_entry(entry_id, delete_results=True)
        self.reload()

    def clear_all(self) -> None:
        api.clear_history(delete_results=True)
        self.reload()
