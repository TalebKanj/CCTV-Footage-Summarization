# -*- coding: utf-8 -*-
"""Settings panel widget for PySide6 UI."""

import json
import os

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QWidget, QDoubleSpinBox, QGroupBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal

from ..theme import get_theme_manager
from ..fonts import get_app_font
from core.config import load_config, AppConfig


class SettingsPanel(QFrame):
    """Settings panel for configuring processing options."""

    settings_changed = Signal(dict)
    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._config = load_config()
        self._load_from_file()
        self._setup_ui()
        self._connect_theme()
    
    def _connect_theme(self):
        theme_manager = get_theme_manager()
        theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme: str):
        self.setStyleSheet(get_theme_manager().get_stylesheet())

    def _load_from_file(self):
        path = self._config.settings_db_path
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self._saved = json.load(f)
        else:
            self._saved = self._get_defaults()

    def _get_defaults(self) -> dict:
        return {
            "pixel_diff_thresh": 15,
            "percent_changed_thresh": 0.15,
            "summary_fps": 12,
            "merge_gap_sec": 2.0,
            "pre_event_sec": 2.0,
            "post_event_sec": 4.0,
            "yolo_confidence": 0.3
        }

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header_widget = QWidget(self)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        icon_label = QLabel("⚙️", header_widget)
        icon_label.setStyleSheet("font-size: 20px;")

        title_label = QLabel("الإعدادات", header_widget)
        title_label.setFont(get_app_font("Bold", 14))

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)

        layout.addWidget(header_widget)
        layout.addWidget(self._create_motion_group())
        layout.addWidget(self._create_segment_group())
        layout.addWidget(self._create_yolo_group())
        layout.addStretch()
        layout.addLayout(self._create_buttons())

    def _create_motion_group(self) -> QGroupBox:
        group = QGroupBox("عدادات الحركة", self)
        group.setFont(get_app_font("Bold", 12))
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        row = QWidget(group)
        row_layout = QHBoxLayout(row)
        row_layout.setSpacing(12)

        lbl = QLabel("عتبة الفروق (px):", row)
        lbl.setFont(get_app_font("Regular", 11))
        self.pixel_diff_spin = QSpinBox(row)
        self.pixel_diff_spin.setRange(5, 100)
        self.pixel_diff_spin.setValue(self._saved.get("pixel_diff_thresh", 15))
        row_layout.addWidget(lbl)
        row_layout.addWidget(self.pixel_diff_spin)

        lbl2 = QLabel("نسبة التغيير (%):", row)
        lbl2.setFont(get_app_font("Regular", 11))
        self.percent_diff_spin = QDoubleSpinBox(row)
        self.percent_diff_spin.setRange(0.01, 1.0)
        self.percent_diff_spin.setSingleStep(0.01)
        self.percent_diff_spin.setValue(self._saved.get("percent_changed_thresh", 0.15))
        row_layout.addWidget(lbl2)
        row_layout.addWidget(self.percent_diff_spin)

        lbl3 = QLabel("معدل الإطارات:", row)
        lbl3.setFont(get_app_font("Regular", 11))
        self.fps_combo = QComboBox(row)
        self.fps_combo.addItems(["6", "12", "24", "30", "60"])
        self.fps_combo.setCurrentText(str(self._saved.get("summary_fps", 12)))
        row_layout.addWidget(lbl3)
        row_layout.addWidget(self.fps_combo)

        layout.addWidget(row)
        return group

    def _create_segment_group(self) -> QGroupBox:
        group = QGroupBox("المقاطع", self)
        group.setFont(get_app_font("Bold", 12))
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        row = QWidget(group)
        row_layout = QHBoxLayout(row)
        row_layout.setSpacing(12)

        lbl = QLabel("الفجوة (ث):", row)
        lbl.setFont(get_app_font("Regular", 11))
        self.merge_gap_spin = QDoubleSpinBox(row)
        self.merge_gap_spin.setRange(0.5, 10.0)
        self.merge_gap_spin.setSingleStep(0.5)
        self.merge_gap_spin.setValue(self._saved.get("merge_gap_sec", 2.0))
        row_layout.addWidget(lbl)
        row_layout.addWidget(self.merge_gap_spin)

        lbl2 = QLabel("قبل الحدث (ث):", row)
        lbl2.setFont(get_app_font("Regular", 11))
        self.pre_event_spin = QDoubleSpinBox(row)
        self.pre_event_spin.setRange(0.0, 10.0)
        self.pre_event_spin.setSingleStep(0.5)
        self.pre_event_spin.setValue(self._saved.get("pre_event_sec", 2.0))
        row_layout.addWidget(lbl2)
        row_layout.addWidget(self.pre_event_spin)

        lbl3 = QLabel("بعد الحدث (ث):", row)
        lbl3.setFont(get_app_font("Regular", 11))
        self.post_event_spin = QDoubleSpinBox(row)
        self.post_event_spin.setRange(0.0, 20.0)
        self.post_event_spin.setSingleStep(0.5)
        self.post_event_spin.setValue(self._saved.get("post_event_sec", 4.0))
        row_layout.addWidget(lbl3)
        row_layout.addWidget(self.post_event_spin)

        layout.addWidget(row)
        return group

    def _create_yolo_group(self) -> QGroupBox:
        group = QGroupBox("الكشف الذكي", self)
        group.setFont(get_app_font("Bold", 12))
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        row = QWidget(group)
        row_layout = QHBoxLayout(row)
        row_layout.setSpacing(12)

        lbl = QLabel("الثقة:", row)
        lbl.setFont(get_app_font("Regular", 11))
        self.yolo_conf_spin = QDoubleSpinBox(row)
        self.yolo_conf_spin.setRange(0.1, 1.0)
        self.yolo_conf_spin.setSingleStep(0.05)
        self.yolo_conf_spin.setValue(self._saved.get("yolo_confidence", 0.3))
        row_layout.addWidget(lbl)
        row_layout.addWidget(self.yolo_conf_spin)

        layout.addWidget(row)
        return group

    def _create_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(8)

        self.save_btn = QPushButton("حفظ الإعدادات", self)
        self.save_btn.setFont(get_app_font("Bold", 11))
        self.save_btn.clicked.connect(self._on_save)

        self.restore_btn = QPushButton("استعادة الافتراضي", self)
        self.restore_btn.setFont(get_app_font("Regular", 11))
        self.restore_btn.clicked.connect(self._on_restore)

        layout.addWidget(self.restore_btn)
        layout.addWidget(self.save_btn)

        return layout

    def _on_save(self):
        settings = self.get_settings()
        self._config = load_config()
        path = self._config.settings_db_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        self.settings_saved.emit()

    def _on_restore(self):
        defaults = self._get_defaults()
        self.pixel_diff_spin.setValue(defaults["pixel_diff_thresh"])
        self.percent_diff_spin.setValue(defaults["percent_changed_thresh"])
        self.fps_combo.setCurrentText(str(defaults["summary_fps"]))
        self.merge_gap_spin.setValue(defaults["merge_gap_sec"])
        self.pre_event_spin.setValue(defaults["pre_event_sec"])
        self.post_event_spin.setValue(defaults["post_event_sec"])
        self.yolo_conf_spin.setValue(defaults["yolo_confidence"])

    def get_settings(self) -> dict:
        return {
            "pixel_diff_thresh": self.pixel_diff_spin.value(),
            "percent_changed_thresh": self.percent_diff_spin.value(),
            "summary_fps": int(self.fps_combo.currentText()),
            "merge_gap_sec": self.merge_gap_spin.value(),
            "pre_event_sec": self.pre_event_spin.value(),
            "post_event_sec": self.post_event_spin.value(),
            "yolo_confidence": self.yolo_conf_spin.value()
        }