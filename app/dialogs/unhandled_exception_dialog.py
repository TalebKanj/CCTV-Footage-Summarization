from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class UnhandledExceptionDialog(QDialog):
    ContinueChoice = 0
    ExitChoice = 1

    def __init__(self, traceback_text: str, parent=None):
        super().__init__(parent)
        self._choice = self.ExitChoice

        self.setWindowTitle("خطأ غير متوقع")
        self.setModal(True)
        self.setMinimumSize(820, 520)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("حدث استثناء غير معالَج", self)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        hint = QLabel(
            "يمكنك المتابعة (تجاهل الخطأ) أو إغلاق التطبيق. قد تؤدي المتابعة إلى سلوك غير مستقر.",
            self,
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("opacity: 0.85;")

        self.trace_edit = QTextEdit(self)
        self.trace_edit.setReadOnly(True)
        self.trace_edit.setPlainText(traceback_text)
        self.trace_edit.setLayoutDirection(Qt.LeftToRight)
        self.trace_edit.setLineWrapMode(QTextEdit.NoWrap)

        fixed = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixed.setPointSize(9)
        self.trace_edit.setFont(fixed)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.copy_btn = QPushButton("نسخ", self)
        self.copy_btn.clicked.connect(self._copy_traceback)

        btn_row.addWidget(self.copy_btn)
        btn_row.addStretch()

        self.continue_btn = QPushButton("متابعة", self)
        self.continue_btn.setObjectName("primary_btn")
        self.continue_btn.clicked.connect(self._on_continue)

        self.exit_btn = QPushButton("خروج", self)
        self.exit_btn.setObjectName("danger_btn")
        self.exit_btn.clicked.connect(self._on_exit)

        btn_row.addWidget(self.continue_btn)
        btn_row.addWidget(self.exit_btn)

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self.trace_edit, 1)
        layout.addLayout(btn_row)

    @property
    def choice(self) -> int:
        return self._choice

    def _copy_traceback(self):
        self.trace_edit.selectAll()
        self.trace_edit.copy()
        self.trace_edit.moveCursor(QTextCursor.Start)

    def _on_continue(self):
        self._choice = self.ContinueChoice
        self.accept()

    def _on_exit(self):
        self._choice = self.ExitChoice
        self.accept()
