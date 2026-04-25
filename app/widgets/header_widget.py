# -*- coding: utf-8 -*-
"""Modern AI Dashboard Header Widget (PySide6)."""

import os
import shutil

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from ..fonts import get_app_font
from ..theme import get_theme_manager


class HeaderWidget(QFrame):

    theme_toggle_requested = Signal()
    clear_cache_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("header")
        self.setFixedHeight(78)

        self._setup_ui()
        self._connect_signals()
        self._apply_style()

    # ================= LOGO =================
    def _create_logo(self, path, parent):
        label = QLabel(parent)

        if path and os.path.exists(path):
            pixmap = QPixmap(path)

            if not pixmap.isNull():
                label.setPixmap(
                    pixmap.scaled(
                        46, 46,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
                return label

        label.setText("📹")
        label.setStyleSheet("font-size: 26px;")
        return label

    # ================= UI =================
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(0)

        # ================= LEFT (LOGO) =================
        left = QWidget(self)
        left_layout = QHBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        app_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        logo_path = os.path.join(app_dir, "assets", "صورة1.png")

        self.logo = self._create_logo(logo_path, left)
        self.logo.setFixedSize(46, 46)

        left_layout.addWidget(self.logo)
        left_layout.addStretch()

        # ================= CENTER (TITLE) =================
        center = QWidget(self)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)

        self.title = QLabel("تلخيص الفديوهات باستخدام تقنيات الذكاء الاصطناعي ", center)
        self.title.setFont(get_app_font("Bold", 15))
        self.title.setAlignment(Qt.AlignCenter)

        self.subtitle = QLabel("لوحة تحكم الذكاء الاصطناعي لتحليل الفيديو", center)
        self.subtitle.setFont(get_app_font("Regular", 13))
        self.subtitle.setAlignment(Qt.AlignCenter)

        center_layout.addWidget(self.title)
        center_layout.addWidget(self.subtitle)

        # ================= RIGHT (THEME + CLEAR BUTTONS) =================
        right = QWidget(self)
        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.clear_btn = QPushButton("🗑️", right)
        self.clear_btn.setFixedSize(70, 46)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setToolTip("مسح ذاكرة التخزين المؤقتة")

        self.theme_btn = QPushButton("🌙", right)
        self.theme_btn.setFixedSize(70, 46)
        self.theme_btn.setCursor(Qt.PointingHandCursor)

        right_layout.addStretch()
        right_layout.addWidget(self.clear_btn)
        right_layout.addWidget(self.theme_btn)

        # ================= MAIN LAYOUT =================
        layout.addWidget(left, 1)
        layout.addWidget(center, 2)
        layout.addWidget(right, 1)

    # ================= STYLE (AI DASHBOARD LOOK) =================
    def _apply_style(self):
        self.setStyleSheet("""
            QFrame#header {
                background: rgba(20, 20, 28, 0.65);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }

            QLabel {
                color: #EDEDED;
                background: transparent;
            }

            QLabel#subtitle {
                color: rgba(255, 255, 255, 0.55);
            }

            QPushButton {
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                background-color: rgba(255, 255, 255, 0.04);
                font-size: 18px;
            }

            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }

            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.18);
            }
        """)

    # ================= SIGNALS =================
    def _connect_signals(self):
        theme_manager = get_theme_manager()
        theme_manager.theme_changed.connect(self._on_theme_changed)
        
        self.theme_btn.clicked.connect(self.theme_toggle_requested)
        self.clear_btn.clicked.connect(self._on_clear_cache)
    
    def _on_theme_changed(self, theme: str):
        self.update_theme_icon(theme == "dark")
        self._apply_style()

    def update_theme_icon(self, is_dark: bool):
        self.theme_btn.setText("🌙" if is_dark else "☀️")

    def _on_clear_cache(self):
        results_dir = "results"
        cache_path = "data/summary_cache.json"
        input_dir = "data/inputs"

        cleared = []

        if os.path.exists(results_dir):
            for item in os.listdir(results_dir):
                item_path = os.path.join(results_dir, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    cleared.append(item_path)
                except Exception:
                    pass

        if os.path.exists(input_dir):
            for item in os.listdir(input_dir):
                item_path = os.path.join(input_dir, item)
                try:
                    if os.path.isfile(item_path):
                        ext = os.path.splitext(item)[1].lower()
                        if ext in ['.mp4', '.avi', '.mov', '.mkv']:
                            os.remove(item_path)
                            cleared.append(item_path)
                except Exception:
                    pass

        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                cleared.append(cache_path)
            except Exception:
                pass

        self.clear_cache_requested.emit()
