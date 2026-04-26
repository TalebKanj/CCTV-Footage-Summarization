from __future__ import annotations

import os
from typing import Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)
from PySide6.QtGui import QFont

import api
from ..theme import apply_card_shadow


class SettingsPanel(QFrame):
    """Summarization controls panel (Arabic-first)."""

    settings_saved = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setLayoutDirection(Qt.RightToLeft)
        apply_card_shadow(self)
        self._setup_ui()
        self.load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title_row = QWidget(self)
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        title_icon = QLabel("🎛️", title_row)
        title_icon.setStyleSheet("font-size: 18px;")
        title = QLabel("التحكم بالتلخيص", title_row)
        title.setStyleSheet("font-size: 14px; font-weight: bold;")

        title_layout.addWidget(title_icon)
        title_layout.addWidget(title)
        title_layout.addStretch()

        layout.addWidget(title_row)

        from PySide6.QtWidgets import QTabWidget
        self.tabs = QTabWidget(self)
        self.tabs.setLayoutDirection(Qt.RightToLeft)

        tab_motion = QWidget()
        l_motion = QVBoxLayout(tab_motion)
        l_motion.addWidget(self._build_motion_group())
        l_motion.addStretch()

        tab_segments = QWidget()
        l_segments = QVBoxLayout(tab_segments)
        l_segments.addWidget(self._build_segments_group())
        l_segments.addStretch()

        tab_detection = QWidget()
        l_detection = QVBoxLayout(tab_detection)
        l_detection.addWidget(self._build_detection_group())
        l_detection.addStretch()

        self.tabs.addTab(tab_motion, "الحركة")
        self.tabs.addTab(tab_segments, "المقاطع")
        self.tabs.addTab(tab_detection, "الكشف الذكي")

        layout.addWidget(self.tabs, 1)
        layout.addLayout(self._build_buttons())

    def _build_motion_group(self) -> QGroupBox:
        group = QGroupBox("إعدادات الحركة", self)
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)

        self.pixel_diff = QSpinBox(group)
        self.pixel_diff.setRange(1, 255)
        self.pixel_diff.setAlignment(Qt.AlignRight)

        self.percent_changed = QDoubleSpinBox(group)
        self.percent_changed.setRange(0.01, 100.0)
        self.percent_changed.setSingleStep(0.01)
        self.percent_changed.setAlignment(Qt.AlignRight)

        self.frame_skip = QSpinBox(group)
        self.frame_skip.setRange(1, 30)
        self.frame_skip.setAlignment(Qt.AlignRight)

        self.resize_width = QSpinBox(group)
        self.resize_width.setRange(160, 1920)
        self.resize_width.setSingleStep(10)
        self.resize_width.setAlignment(Qt.AlignRight)

        self.morph_kernel = QSpinBox(group)
        self.morph_kernel.setRange(1, 15)
        self.morph_kernel.setSingleStep(2)
        self.morph_kernel.setAlignment(Qt.AlignRight)

        self.morph_open = QSpinBox(group)
        self.morph_open.setRange(0, 5)
        self.morph_open.setAlignment(Qt.AlignRight)

        self.morph_dilate = QSpinBox(group)
        self.morph_dilate.setRange(0, 5)
        self.morph_dilate.setAlignment(Qt.AlignRight)

        self.pixel_diff.setToolTip("عتبة اختلاف البكسل للكشف عن الحركة.")
        self.percent_changed.setToolTip("نسبة التغير المطلوبة لاعتبار الإطار متحركاً.")
        self.morph_open.setToolTip("إزالة الضوضاء الصغيرة (Opening).")

        form.addRow("عتبة الفرق (px):", self.pixel_diff)
        form.addRow("نسبة التغير (%):", self.percent_changed)
        form.addRow("تخطي الإطارات:", self.frame_skip)
        form.addRow("عرض التحجيم:", self.resize_width)
        form.addRow("نواة المرشح:", self.morph_kernel)
        form.addRow("فتح (iterations):", self.morph_open)
        form.addRow("تمديد (iterations):", self.morph_dilate)
        return group

    def _build_segments_group(self) -> QGroupBox:
        group = QGroupBox("إعدادات المقاطع", self)
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)

        self.summary_fps = QSpinBox(group)
        self.summary_fps.setRange(1, 120)
        self.summary_fps.setAlignment(Qt.AlignRight)

        self.merge_gap = QDoubleSpinBox(group)
        self.merge_gap.setRange(0.0, 30.0)
        self.merge_gap.setSingleStep(0.5)
        self.merge_gap.setAlignment(Qt.AlignRight)

        self.pre_event = QDoubleSpinBox(group)
        self.pre_event.setRange(0.0, 30.0)
        self.pre_event.setSingleStep(0.5)
        self.pre_event.setAlignment(Qt.AlignRight)

        self.post_event = QDoubleSpinBox(group)
        self.post_event.setRange(0.0, 60.0)
        self.post_event.setSingleStep(0.5)
        self.post_event.setAlignment(Qt.AlignRight)

        self.merge_gap.setToolTip("الفجوة الزمنية القصوى لدمج المقاطع المتقاربة.")
        self.pre_event.setToolTip("عدد الثواني المضافة قبل بداية الحدث.")
        self.post_event.setToolTip("عدد الثواني المضافة بعد نهاية الحدث.")

        form.addRow("FPS الملخص:", self.summary_fps)
        form.addRow("الفجوة (ث):", self.merge_gap)
        form.addRow("قبل الحدث (ث):", self.pre_event)
        form.addRow("بعد الحدث (ث):", self.post_event)
        return group

    def _build_detection_group(self) -> QGroupBox:
        group = QGroupBox("الكشف الذكي (اختياري)", self)
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)

        self.enable_detection = QCheckBox("تفعيل YOLO على الإطارات المحددة", group)

        self.yolo_conf = QDoubleSpinBox(group)
        self.yolo_conf.setRange(0.01, 1.0)
        self.yolo_conf.setSingleStep(0.05)
        self.yolo_conf.setAlignment(Qt.AlignRight)

        self.allowed_classes = QLineEdit(group)
        self.allowed_classes.setPlaceholderText("person,car")
        self.allowed_classes.setAlignment(Qt.AlignRight)

        form.addRow(self.enable_detection)
        form.addRow("الثقة:", self.yolo_conf)
        form.addRow("الفئات المسموحة:", self.allowed_classes)

        # Model size dropdown (preferred) + optional custom path.
        self.yolo_model_size = QComboBox(group)
        self.yolo_model_size.setLayoutDirection(Qt.RightToLeft)
        self._yolo_size_to_file = {
            "yolov8n": "yolov8n.pt",
            "yolov8s": "yolov8s.pt",
            "yolov8m": "yolov8m.pt",
            "yolov8l": "yolov8l.pt",
            "yolov8x": "yolov8x.pt",
        }
        self._yolo_known_files = set(self._yolo_size_to_file.values())
        self.yolo_model_size.addItem("YOLOv8n (سريع)", "yolov8n")
        self.yolo_model_size.addItem("YOLOv8s (خفيف)", "yolov8s")
        self.yolo_model_size.addItem("YOLOv8m (متوازن)", "yolov8m")
        self.yolo_model_size.addItem("YOLOv8l (دقيق)", "yolov8l")
        self.yolo_model_size.addItem("YOLOv8x (أدق)", "yolov8x")
        self.yolo_model_size.addItem("مخصص…", "__custom__")
        self.yolo_model_size.currentIndexChanged.connect(self._on_yolo_model_changed)
        form.addRow("حجم النموذج:", self.yolo_model_size)

        self.yolo_model_path = QLineEdit(group)
        self.yolo_model_path.setPlaceholderText("models/yolov8x.pt")
        self.yolo_model_path.setAlignment(Qt.AlignRight)
        self.yolo_model_path.setReadOnly(True)
        browse = QPushButton("اختيار ملف", group)
        browse.clicked.connect(self._browse_yolo_weights)
        self._browse_yolo_btn = browse

        row = QWidget(group)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        row_layout.addWidget(self.yolo_model_path, 1)
        row_layout.addWidget(browse, 0)

        form.addRow("مسار النموذج:", row)

        self.hf_token = QLineEdit(group)
        self.hf_token.setAlignment(Qt.AlignRight)
        self.hf_token.setPlaceholderText("اختياري: لإتاحة تنزيل النموذج من HuggingFace")
        try:
            self.hf_token.setEchoMode(QLineEdit.Password)
        except Exception:
            pass
        hint = QLabel("سيتم حفظ الرمز محلياً في الإعدادات. اتركه فارغاً إذا لم يلزم.", group)
        hint.setStyleSheet("opacity: 0.8;")
        hint.setWordWrap(True)

        form.addRow("HuggingFace Token:", self.hf_token)
        form.addRow("", hint)
        return group

    def _browse_yolo_weights(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "اختر ملف النموذج", "", "PyTorch Weights (*.pt);;All Files (*)")
        if path:
            self.yolo_model_path.setText(path)
            try:
                idx = self.yolo_model_size.findData("__custom__")
                if idx >= 0:
                    self.yolo_model_size.setCurrentIndex(idx)
            except Exception:
                pass
            self._apply_yolo_mode()

    def _build_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        self.restore_btn = QPushButton("استعادة الافتراضي", self)
        self.restore_btn.clicked.connect(self.restore_defaults)

        self.save_btn = QPushButton("حفظ الإعدادات", self)
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.clicked.connect(self.save_settings)

        row.addWidget(self.restore_btn)
        row.addStretch()
        row.addWidget(self.save_btn)
        return row

    def load_settings(self) -> None:
        settings = api.load_settings()
        self._apply_settings(settings)

    def restore_defaults(self) -> None:
        defaults = api.get_default_config()
        self._apply_settings(defaults)

    def _apply_settings(self, s: Dict) -> None:
        self.pixel_diff.setValue(int(s.get("pixel_diff_thresh", 28)))
        self.percent_changed.setValue(float(s.get("percent_changed_thresh", 1.2)))
        self.frame_skip.setValue(int(s.get("frame_skip", 3)))
        self.resize_width.setValue(int(s.get("resize_width", 640)))
        self.morph_kernel.setValue(int(s.get("morph_kernel", 5)))
        self.morph_open.setValue(int(s.get("morph_open_iters", 2)))
        self.morph_dilate.setValue(int(s.get("morph_dilate_iters", 2)))

        self.summary_fps.setValue(int(s.get("summary_fps", 12)))
        self.merge_gap.setValue(float(s.get("merge_gap_sec", 2.0)))
        self.pre_event.setValue(float(s.get("pre_event_sec", 2.0)))
        self.post_event.setValue(float(s.get("post_event_sec", 4.0)))

        self.enable_detection.setChecked(bool(s.get("enable_object_detection", False)))
        self.yolo_conf.setValue(float(s.get("yolo_confidence", 0.3)))
        self.yolo_model_path.setText(str(s.get("yolo_model_path", "models/yolov8x.pt")))
        self.hf_token.setText(str(s.get("hf_token") or ""))
        allowed = s.get("allowed_classes", ["person", "car"])
        if isinstance(allowed, list):
            self.allowed_classes.setText(",".join(allowed))
        else:
            self.allowed_classes.setText(str(allowed))

        # Sync dropdown selection with saved settings.
        filename = str(s.get("yolo_model_filename") or "").strip()
        path = str(s.get("yolo_model_path") or "").strip()
        base = os.path.basename(path) if path else ""
        chosen_file = filename or base
        if hasattr(self, "yolo_model_size"):
            if chosen_file in getattr(self, "_yolo_known_files", set()):
                size_key = next((k for k, v in self._yolo_size_to_file.items() if v == chosen_file), None)
                if size_key:
                    idx = self.yolo_model_size.findData(size_key)
                    if idx >= 0:
                        self.yolo_model_size.setCurrentIndex(idx)
            elif chosen_file:
                idx = self.yolo_model_size.findData("__custom__")
                if idx >= 0:
                    self.yolo_model_size.setCurrentIndex(idx)
            self._apply_yolo_mode()

    def get_settings(self) -> dict:
        allowed = [c.strip() for c in self.allowed_classes.text().split(",") if c.strip()]
        model_repo = "Ultralytics/YOLOv8"
        size_key = self.yolo_model_size.currentData() if hasattr(self, "yolo_model_size") else "__custom__"
        if size_key in getattr(self, "_yolo_size_to_file", {}):
            model_filename = self._yolo_size_to_file[size_key]
            model_path = os.path.join("models", model_filename)
        else:
            model_path = self.yolo_model_path.text().strip() or "models/yolov8x.pt"
            model_filename = os.path.basename(model_path) or "yolov8x.pt"
        return {
            "pixel_diff_thresh": self.pixel_diff.value(),
            "percent_changed_thresh": self.percent_changed.value(),
            "frame_skip": self.frame_skip.value(),
            "resize_width": self.resize_width.value(),
            "morph_kernel": self.morph_kernel.value(),
            "morph_open_iters": self.morph_open.value(),
            "morph_dilate_iters": self.morph_dilate.value(),
            "summary_fps": self.summary_fps.value(),
            "merge_gap_sec": self.merge_gap.value(),
            "pre_event_sec": self.pre_event.value(),
            "post_event_sec": self.post_event.value(),
            "enable_object_detection": self.enable_detection.isChecked(),
            "yolo_confidence": self.yolo_conf.value(),
            "allowed_classes": allowed or ["person", "car"],
            "yolo_model_repo": model_repo,
            "yolo_model_filename": model_filename,
            "yolo_model_path": model_path,
            "hf_token": self.hf_token.text().strip() or None,
        }

    def _on_yolo_model_changed(self) -> None:
        self._apply_yolo_mode()

    def _apply_yolo_mode(self) -> None:
        if not hasattr(self, "yolo_model_size"):
            return
        key = self.yolo_model_size.currentData()
        is_custom = key == "__custom__"
        try:
            self.yolo_model_path.setReadOnly(not is_custom)
        except Exception:
            pass
        try:
            self._browse_yolo_btn.setEnabled(is_custom)
        except Exception:
            pass
        if not is_custom and key in self._yolo_size_to_file:
            filename = self._yolo_size_to_file[key]
            self.yolo_model_path.setText(os.path.join("models", filename))

    def save_settings(self) -> None:
        normalized = api.save_settings(self.get_settings())
        self.settings_saved.emit(normalized)
