# -*- coding: utf-8 -*-
"""Upload panel widget for PySide6 UI - Unified Border Styling Edition."""

import os
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFileDialog, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap, QColor

from ..utils import compute_file_hash, format_file_size, VIDEO_FILTER
from ..fonts import get_app_font


class UploadPanel(QFrame):
    """لوحة إدارة الملفات بتصميم موحد حيث تتطابق الحدود الداخلية مع الحدود الخارجية تماماً."""

    file_selected = Signal(str)
    process_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("main_panel")
        self.setFixedWidth(440)
        self._current_file = None
        self._is_processing = False
        self._setup_ui()
        self._apply_styles()

    def _apply_styles(self):
        # توحيد نمط البوردر الذهبي الخافت للهوية الوطنية الجديدة
        unified_border = "1px solid rgba(185, 167, 121, 0.4)"
        
        self.setStyleSheet(f"""
            QFrame#main_panel {{
                background-color: #002623;
                border: {unified_border}; 
                border-radius: 40px;
            }}

            /* العنوان العلوي - نفس البوردر الخارجي */
            QLabel#panel_title {{
                color: #b9a779;
                border: {unified_border};
                border-radius: 12px;
                padding: 8px 25px;
                background-color: rgba(22, 22, 22, 0.5);
            }}

            /* منطقة الرفع/العرض - نفس البوردر الخارجي */
            QFrame#drop_zone {{
                background-color: #161616;
                border: {unified_border};
                border-radius: 25px;
            }}
            
            QLabel#video_preview {{
                color: rgba(185, 167, 121, 0.4);
                background: transparent;
            }}

            /* بطاقة المعلومات - نفس البوردر الخارجي */
            QWidget#info_card {{
                background-color: rgba(22, 22, 22, 0.6);
                border: {unified_border};
                border-radius: 20px;
                padding: 15px;
            }}
            
            QLabel#info_label {{ color: #b9a779; font-size: 10px; font-weight: bold; }}
            QLabel#info_value {{ color: #edebe0; font-size: 11px; }}

            /* زر الإجراء الرئيسي - نفس البوردر الخارجي */
            QPushButton#process_btn {{
                background-color: #161616; 
                color: #b9a779;
                border: {unified_border};
                border-radius: 20px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton#process_btn:hover {{ 
                background-color: #b9a779; 
                color: #161616; 
                border: 1px solid #edebe0;
            }}
            QPushButton#process_btn:disabled {{ 
                border-color: rgba(61, 58, 59, 0.4); 
                color: #3d3a3b; 
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(185, 167, 121, 25))
        self.setGraphicsEffect(shadow)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 45, 40, 45)
        main_layout.setSpacing(35)

        # 1. العنوان
        title_container = QHBoxLayout()
        self.title_lbl = QLabel("إدارة ملفات النظام")
        self.title_lbl.setObjectName("panel_title")
        self.title_lbl.setFont(get_app_font("Bold", 12))
        title_container.addStretch()
        title_container.addWidget(self.title_lbl)
        title_container.addStretch()
        main_layout.addLayout(title_container)

        # 2. منطقة الرفع/العرض
        self.drop_zone = QFrame()
        self.drop_zone.setObjectName("drop_zone")
        self.drop_zone.setFixedHeight(220)
        self.drop_zone.setCursor(Qt.PointingHandCursor)
        self.drop_zone.mousePressEvent = lambda e: self._select_file()

        dz_layout = QVBoxLayout(self.drop_zone)
        self.video_preview = QLabel("انقر لتحميل بيانات الفيديو")
        self.video_preview.setObjectName("video_preview")
        self.video_preview.setAlignment(Qt.AlignCenter)
        self.video_preview.setFont(get_app_font("Medium", 11))
        
        dz_layout.addWidget(self.video_preview)
        main_layout.addWidget(self.drop_zone)

        # 3. بطاقة المعلومات
        self.info_box = QWidget()
        self.info_box.setObjectName("info_card")
        self.info_box.setVisible(False)
        info_layout = QVBoxLayout(self.info_box)
        info_layout.setSpacing(12)
        
        self.widgets = {}
        for ar_text, key in [("اسم الملف", "FILE"), ("حجم الملف", "SIZE"), ("بصمة التحقق", "HASH")]:
            row = QHBoxLayout()
            val = QLabel("-")
            val.setObjectName("info_value")
            lbl = QLabel(ar_text)
            lbl.setObjectName("info_label")
            row.addWidget(val, 0, Qt.AlignLeft)
            row.addStretch()
            row.addWidget(lbl, 0, Qt.AlignRight)
            info_layout.addLayout(row)
            self.widgets[key] = val
        main_layout.addWidget(self.info_box)

        # 4. الزر
        self.process_btn = QPushButton("بدء التحليل الذكي")
        self.process_btn.setObjectName("process_btn")
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(lambda: self.process_requested.emit(self._current_file))
        main_layout.addWidget(self.process_btn)

        main_layout.addStretch()

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر الفيديو", "", VIDEO_FILTER)
        if path and os.path.exists(path):
            self._set_file(path)

    def _set_file(self, path: str):
        self._current_file = path
        name = os.path.basename(path)
        self.widgets["FILE"].setText(name[:25] + "..." if len(name) > 25 else name)
        self.widgets["SIZE"].setText(format_file_size(os.path.getsize(path)))
        self.widgets["HASH"].setText(compute_file_hash(path)[:12])
        self.info_box.setVisible(True)
        self.process_btn.setEnabled(True)
        self._load_preview(path)
        self.file_selected.emit(path)

    def _load_preview(self, path):
        try:
            import cv2
            cap = cv2.VideoCapture(path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                pix = QPixmap.fromImage(img).scaled(380, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.video_preview.setPixmap(pix)
        except Exception:
            self.video_preview.setText("المعاينة غير متاحة")

    def set_processing(self, processing: bool):
        """Set the processing state of the panel."""
        self._is_processing = processing
        
        if processing:
            self.process_btn.setEnabled(False)
            self.drop_zone.setEnabled(False)
            self.drop_zone.setCursor(Qt.ForbiddenCursor)
            self.widgets["FILE"].setText("جاري المعالجة...")
            self.widgets["SIZE"].setText("-")
            self.widgets["HASH"].setText("-")
        else:
            self.drop_zone.setEnabled(True)
            self.drop_zone.setCursor(Qt.PointingHandCursor)
            
            if self._current_file and os.path.exists(self._current_file):
                self.widgets["FILE"].setText(os.path.basename(self._current_file))
                self.widgets["SIZE"].setText(format_file_size(os.path.getsize(self._current_file)))
                self.widgets["HASH"].setText(compute_file_hash(self._current_file)[:12])
                self.process_btn.setEnabled(True)
            else:
                self.widgets["FILE"].setText("-")
                self.widgets["SIZE"].setText("-")
                self.widgets["HASH"].setText("-")
                self.process_btn.setEnabled(False)

    def is_processing(self) -> bool:
        """Return whether the panel is currently in processing state."""
        return self._is_processing

    def clear(self):
        """Clear the upload panel to reset to starting point."""
        self._current_file = None
        self._is_processing = False
        self.info_box.setVisible(False)
        self.process_btn.setEnabled(False)
        self.video_preview.setText("انقر لتحميل بيانات الفيديو")
        self.file_selected.emit("")