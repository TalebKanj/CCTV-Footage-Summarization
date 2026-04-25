# -*- coding: utf-8 -*-
"""Result panel widget for PySide6 UI - Color Matched Edition."""

import os
import cv2
import shutil
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QWidget, QGraphicsDropShadowEffect, QMessageBox, QSlider
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QColor
from PySide6.QtWidgets import QSizePolicy

from ..state import app_state
from ..fonts import get_app_font
from ..theme import get_theme_manager


class ResultPanel(QFrame):
    """لوحة نتائج بتنسيق لوني مطابق تماماً لمركز الرفع لضمان الوحدة البصرية."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("result_panel")
        self._result = None
        self._thumbnail_loaded = False
        self._video_capture = None
        self._video_fps = 12
        self._total_frames = 0
        self._current_frame = 0
        self._is_playing = False
        self._playback_timer = None
        self._setup_ui()
        self._apply_styles()
        self._connect_theme()
    
    def _connect_theme(self):
        theme_manager = get_theme_manager()
        theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme: str):
        self._apply_styles()

    def _apply_styles(self):
        unified_border = "1px solid rgba(185, 167, 121, 0.4)"
        charcoal_bg = "#161616" # اللون المطابق للوحة الرفع
        
        self.setStyleSheet(f"""
            QFrame#result_panel {{
                background-color: #002623;
                border: {unified_border};
                border-radius: 40px;
            }}
            
            QLabel#result_title {{
                color: #b9a779;
                border: {unified_border};
                border-radius: 12px;
                padding: 8px 30px;
                background-color: rgba(22, 22, 22, 0.5);
            }}

            /* شاشة العرض - تم توحيد لونها مع لوحة الرفع */
            QFrame#viewport_frame {{
                background-color: {charcoal_bg};
                border: {unified_border};
                border-radius: 30px;
            }}

            QLabel#placeholder_text {{
                color: rgba(185, 167, 121, 0.4);
                background: transparent;
            }}

            QPushButton#action_btn {{
                background-color: {charcoal_bg}; 
                color: #b9a779;
                border: {unified_border};
                border-radius: 18px;
                padding: 14px 25px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton#action_btn:hover {{
                background-color: #b9a779;
                color: #161616;
                border: 1px solid #edebe0;
            }}
            QPushButton#action_btn:disabled {{
                border-color: rgba(61, 58, 59, 0.4);
                color: #3d3a3b;
            }}

            QPushButton#play_btn {{
                background-color: #161616;
                color: #b9a779;
                border: {unified_border};
                border-radius: 15px;
                padding: 10px 20px;
                font-size: 13px;
            }}
            QPushButton#play_btn:hover {{
                background-color: #b9a779;
                color: #161616;
            }}
            QPushButton#play_btn:disabled {{
                border-color: rgba(61, 58, 59, 0.4);
                color: #3d3a3b;
            }}

            QSlider#seek_slider {{
                border: none;
                background: transparent;
            }}
            QSlider#seek_slider::groove:horizontal {{
                border: 1px solid rgba(185, 167, 121, 0.4);
                background: transparent;
                height: 6px;
                border-radius: 3px;
            }}
            QSlider#seek_slider::handle:horizontal {{
                background: #b9a779;
                border: none;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider#seek_slider::add-page:horizontal {{
                background: rgba(185, 167, 121, 0.3);
                border-radius: 3px;
            }}
            QSlider#seek_slider::sub-page:horizontal {{
                background: #b9a779;
                border-radius: 3px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(185, 167, 121, 20))
        self.setGraphicsEffect(shadow)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 45, 40, 45)
        main_layout.setSpacing(0)

        title_layout = QHBoxLayout()
        self.title_lbl = QLabel("مخرجات تحليل النظام")
        self.title_lbl.setObjectName("result_title")
        self.title_lbl.setFont(get_app_font("Bold", 12))
        title_layout.addStretch()
        title_layout.addWidget(self.title_lbl)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        main_layout.addSpacing(50)

        self.viewport_frame = QFrame()
        self.viewport_frame.setObjectName("viewport_frame")
        viewport_layout = QVBoxLayout(self.viewport_frame)
        viewport_layout.setAlignment(Qt.AlignCenter)

        self.placeholder_lbl = QLabel("بانتظار رفع الفيديو للتلخيص")
        self.placeholder_lbl.setObjectName("placeholder_text")
        self.placeholder_lbl.setAlignment(Qt.AlignCenter)
        self.placeholder_lbl.setFont(get_app_font("Medium", 12))
        
        self.video_display = QLabel()
        self.video_display.setAlignment(Qt.AlignCenter)
        self.video_display.setVisible(False)
        self.video_display.setMinimumSize(640, 400)
        
        controls_widget = QWidget()
        controls_widget.setObjectName("controls_widget")
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 10, 0, 0)
        controls_layout.setSpacing(8)
        
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setObjectName("seek_slider")
        self.seek_slider.setRange(0, 100)
        self.seek_slider.setValue(0)
        self.seek_slider.setEnabled(False)
        
        time_layout = QHBoxLayout()
        self.time_lbl = QLabel("00:00 / 00:00")
        self.time_lbl.setStyleSheet("color: #b9a779; font-size: 11px;")
        
        self.rewind_btn = QPushButton("⏪")
        self.rewind_btn.setFixedWidth(40)
        self.rewind_btn.setStyleSheet("font-size: 14px; border: none; background: transparent;")
        
        self.forward_btn = QPushButton("⏩")
        self.forward_btn.setFixedWidth(40)
        self.forward_btn.setStyleSheet("font-size: 14px; border: none; background: transparent;")
        
        time_layout.addWidget(self.rewind_btn)
        time_layout.addWidget(self.time_lbl)
        time_layout.addWidget(self.forward_btn)
        time_layout.addStretch()
        
        self.play_btn = QPushButton("▶️ تشغيل")
        self.play_btn.setObjectName("play_btn")
        self.play_btn.setEnabled(False)
        self.play_btn.setFixedWidth(120)
        
        controls_layout.addWidget(self.seek_slider)
        controls_layout.addLayout(time_layout)
        controls_layout.addWidget(self.play_btn)
        controls_layout.setAlignment(self.play_btn, Qt.AlignCenter)
        
        controls_widget.setVisible(False)
        
        viewport_layout.addWidget(self.placeholder_lbl)
        viewport_layout.addWidget(self.video_display)
        viewport_layout.addWidget(controls_widget)
        main_layout.addWidget(self.viewport_frame, 1)

        main_layout.addSpacing(50)

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(20)
        btns_layout.addStretch()

        self.export_frames_btn = QPushButton("تصدير الإطارات")
        self.export_frames_btn.setObjectName("action_btn")
        self.export_frames_btn.setEnabled(False)

        self.export_video_btn = QPushButton("تصدير الملخص النهائي")
        self.export_video_btn.setObjectName("action_btn")
        self.export_video_btn.setEnabled(False)

        btns_layout.addWidget(self.export_frames_btn)
        btns_layout.addWidget(self.export_video_btn)
        
        main_layout.addLayout(btns_layout)

        self.export_video_btn.clicked.connect(self._on_download_video)
        self.export_frames_btn.clicked.connect(self._on_download_frames)
        self.play_btn.clicked.connect(self._on_play_pause)
        self.seek_slider.sliderMoved.connect(self._on_seek)
        self.rewind_btn.clicked.connect(self._on_rewind)
        self.forward_btn.clicked.connect(self._on_forward)

    def set_result(self, result: dict):
        if self._result is result:
            return
        self._stop_playback()
        self._result = result
        self._thumbnail_loaded = False
        try:
            segments_path = result.get("segments_video", "")
            if result and segments_path and os.path.exists(segments_path):
                self.placeholder_lbl.setVisible(False)
                self.video_display.setVisible(True)
                self._init_video_playback(segments_path)
                self.export_video_btn.setEnabled(True)
                frames_path = result.get("frames_video", "")
                self.export_frames_btn.setEnabled(bool(frames_path and os.path.exists(frames_path)))
                app_state.result = result
            else:
                self.clear()
        except Exception as e:
            print(f"[DEBUG] Error in set_result: {e}")
            self.clear()

    def _init_video_playback(self, video_path: str):
        if self._video_capture:
            self._video_capture.release()
        self._video_capture = cv2.VideoCapture(video_path)
        if not self._video_capture.isOpened():
            print(f"[DEBUG] Failed to open video: {video_path}")
            return
        self._total_frames = int(self._video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self._video_fps = self._video_capture.get(cv2.CAP_PROP_FPS) or 12
        self._current_frame = 0
        self._is_playing = False
        self.seek_slider.setRange(0, max(1, self._total_frames - 1))
        self.seek_slider.setValue(0)
        self.seek_slider.setEnabled(True)
        self.play_btn.setEnabled(True)
        self.play_btn.setText("▶️ تشغيل")
        for w in self.viewport_frame.findChildren(QWidget):
            if w.objectName() == "controls_widget":
                w.setVisible(True)
                break
        self._display_frame()
        self._update_time_label()

    def _format_time(self, frame_idx: int) -> str:
        """Format frame index to MM:SS."""
        total_seconds = int(frame_idx / max(1, self._video_fps))
        mins, secs = divmod(total_seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    def _update_time_label(self):
        """Update the time label with current/total time."""
        if not self._total_frames or not self._video_fps:
            return
        current_time = self._format_time(self._current_frame)
        total_time = self._format_time(self._total_frames)
        self.time_lbl.setText(f"{current_time} / {total_time}")

    def _display_frame(self):
        if not self._video_capture or not self._video_capture.isOpened():
            return
        self._video_capture.set(cv2.CAP_PROP_POS_FRAMES, self._current_frame)
        ret, frame = self._video_capture.read()
        if ret and frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(img).scaled(800, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_display.setPixmap(pix)
            self.video_display.setStyleSheet("border: 1px solid rgba(185, 167, 121, 0.4); border-radius: 25px;")
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(self._current_frame)
            self.seek_slider.blockSignals(False)
            self._update_time_label()

    def _on_play_pause(self):
        if self._is_playing:
            self._pause_playback()
        else:
            self._start_playback()

    def _start_playback(self):
        if not self._video_capture:
            return
        self._is_playing = True
        self.play_btn.setText("⏸️ إيقاف")
        if not self._playback_timer:
            self._playback_timer = QTimer(self)
            self._playback_timer.timeout.connect(self._advance_frame)
        interval = int(1000 / max(1, self._video_fps))
        self._playback_timer.start(interval)

    def _pause_playback(self):
        self._is_playing = False
        self.play_btn.setText("▶️ تشغيل")
        if self._playback_timer:
            self._playback_timer.stop()

    def _stop_playback(self):
        self._pause_playback()
        if self._video_capture:
            self._video_capture.release()
            self._video_capture = None
        self._thumbnail_loaded = False
        self.seek_slider.setEnabled(False)
        self.play_btn.setEnabled(False)
        self.play_btn.setText("▶️ تشغيل")
        self._is_playing = False
        self._current_frame = 0
        self._total_frames = 0

    def _advance_frame(self):
        if not self._video_capture or not self._is_playing:
            return
        self._current_frame += 1
        if self._current_frame >= self._total_frames:
            self._current_frame = 0
        self._display_frame()

    def _on_seek(self, position: int):
        if not self._video_capture:
            return
        self._current_frame = position
        self._display_frame()

    def _on_rewind(self):
        if not self._video_capture:
            return
        self._pause_playback()
        skip_frames = int(self._video_fps * 5)
        self._current_frame = max(0, self._current_frame - skip_frames)
        self._display_frame()

    def _on_forward(self):
        if not self._video_capture:
            return
        self._pause_playback()
        skip_frames = int(self._video_fps * 5)
        self._current_frame = min(self._total_frames - 1, self._current_frame + skip_frames)
        self._display_frame()

    def clear(self):
        self._stop_playback()
        self._result = None
        self.video_display.setVisible(False)
        self.placeholder_lbl.setVisible(True)
        self.export_video_btn.setEnabled(False)
        self.export_frames_btn.setEnabled(False)
        self.time_lbl.setText("00:00 / 00:00")
        for w in self.viewport_frame.findChildren(QWidget):
            if w.objectName() == "" and isinstance(w, QWidget):
                for child in w.children():
                    if isinstance(child, (QSlider, QPushButton)):
                        child.setVisible(False)
                break
        app_state.result = None

    def _on_download_video(self):
        self._save_file("segments_video", "تحميل ملخص الفيديو", "summary_output.mp4")

    def _on_download_frames(self):
        self._save_file("frames_video", "تحميل إطارات المعالجة", "frames_output.mp4")

    def _save_file(self, key, title, default_name):
        if not self._result:
            return
        
        source_path = self._result.get(key, "")
        if not source_path or not os.path.exists(source_path):
            QMessageBox.warning(self, "خطأ", "الملف المصدر غير موجود")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, title, default_name, "Video Files (*.mp4)"
        )
        if not save_path:
            return
        
        if not save_path.endswith('.mp4'):
            save_path += '.mp4'
        
        if os.path.exists(save_path):
            reply = QMessageBox.question(
                self, "تأكيد الاستبدال",
                "الملف موجود بالفعل. هل تريد استبداله؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        try:
            shutil.copy(source_path, save_path)
            QMessageBox.information(
                self, "نجاح",
                f"تم تصدير الملف بنجاح:\n{save_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "خطأ",
                f"فشل تصدير الملف:\n{str(e)}"
            )