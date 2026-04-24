# -*- coding: utf-8 -*-
"""Settings panel widget for PySide6 UI."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QWidget
)
from PySide6.QtCore import Qt, Signal

from ..theme import get_theme_manager
from ..fonts import get_app_font


class SettingsPanel(QFrame):
    """Settings panel for configuring processing options."""

    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()

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

        title_label = QLabel("Settings", header_widget)
        title_label.setFont(get_app_font("Bold", 14))

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)

        layout.addWidget(header_widget)
        layout.addWidget(self._create_threshold_setting())
        layout.addWidget(self._create_fps_setting())
        layout.addStretch()

    def _create_threshold_setting(self):
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel("Motion Threshold (%)", widget)
        label.setFont(get_app_font("Regular", 12))

        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(8)

        self.threshold_slider = QSlider(Qt.Horizontal, widget)
        self.threshold_slider.setRange(1, 50)
        self.threshold_slider.setValue(15)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)

        self.threshold_value = QLabel("15%", widget)
        self.threshold_value.setFont(get_app_font("Bold", 12))
        self.threshold_value.setStyleSheet("min-width: 40px;")

        slider_layout.addWidget(self.threshold_slider)
        slider_layout.addWidget(self.threshold_value)

        layout.addWidget(label)
        layout.addLayout(slider_layout)

        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_value.setText(f"{v}%")
        )

        return widget

    def _create_fps_setting(self):
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel("Output Video FPS", widget)
        label.setFont(get_app_font("Regular", 12))

        self.fps_combo = QComboBox(widget)
        self.fps_combo.addItems(["6", "12", "24", "30", "60"])
        self.fps_combo.setCurrentText("12")

        layout.addWidget(label)
        layout.addWidget(self.fps_combo)

        return widget

    def get_settings(self) -> dict:
        return {
            "threshold": self.threshold_slider.value() / 100.0,
            "fps": int(self.fps_combo.currentText()),
        }