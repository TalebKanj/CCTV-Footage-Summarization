from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..theme import apply_card_shadow


def _format_time_ms(ms: int) -> str:
    if ms <= 0:
        return "00:00"
    s = int(ms // 1000)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}" if h > 0 else f"{m:02d}:{sec:02d}"


class _MediaPlayerWidget(QFrame):
    """QtMultimedia-based player with a standard slider/time/volume control bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setLayoutDirection(Qt.RightToLeft)
        apply_card_shadow(self)

        self._player = None
        self._audio = None
        self._video = None
        self._has_media = False
        self._dragging = False

        self._setup_ui()
        self._init_player()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.placeholder = QLabel("لا يوجد فيديو ملخص بعد.", self)
        self.placeholder.setObjectName("video_view")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setMinimumHeight(280)
        self.placeholder.setWordWrap(True)
        layout.addWidget(self.placeholder, 1)

        self.controls = QWidget(self)
        row = QHBoxLayout(self.controls)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self.play_btn = QToolButton(self.controls)
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.setToolTip("تشغيل/إيقاف مؤقت")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self._toggle_play_pause)

        self.stop_btn = QToolButton(self.controls)
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_btn.setToolTip("إيقاف")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop)

        self.pos_slider = QSlider(Qt.Horizontal, self.controls)
        self.pos_slider.setRange(0, 0)
        self.pos_slider.setEnabled(False)
        self.pos_slider.sliderPressed.connect(self._on_seek_start)
        self.pos_slider.sliderReleased.connect(self._on_seek_end)
        self.pos_slider.sliderMoved.connect(self._on_seek_move)
        self.pos_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.time_label = QLabel("00:00 / 00:00", self.controls)
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.vol_btn = QToolButton(self.controls)
        self.vol_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.vol_btn.setToolTip("الصوت")
        self.vol_btn.setEnabled(False)
        self.vol_btn.clicked.connect(self._toggle_mute)

        self.vol_slider = QSlider(Qt.Horizontal, self.controls)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(60)
        self.vol_slider.setFixedWidth(120)
        self.vol_slider.setEnabled(False)
        self.vol_slider.valueChanged.connect(self._on_volume_changed)

        row.addWidget(self.play_btn)
        row.addWidget(self.stop_btn)
        row.addWidget(self.pos_slider, 1)
        row.addWidget(self.time_label)
        row.addWidget(self.vol_btn)
        row.addWidget(self.vol_slider)

        layout.addWidget(self.controls, 0)

    def _init_player(self) -> None:
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
            from PySide6.QtMultimediaWidgets import QVideoWidget
        except Exception:
            self.placeholder.setText("QtMultimedia غير متاح على هذا النظام.")
            return

        self._audio = QAudioOutput(self)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._audio)

        self._video = QVideoWidget(self)
        self._video.setMinimumHeight(280)
        self._video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._player.setVideoOutput(self._video)

        # Replace placeholder with video widget.
        self.layout().replaceWidget(self.placeholder, self._video)  # type: ignore[union-attr]
        self.placeholder.hide()
        self._video.hide()

        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)
        try:
            self._player.errorOccurred.connect(self._on_error)  # type: ignore[attr-defined]
        except Exception:
            pass

        # Space toggles play/pause.
        try:
            self.play_btn.setShortcut(QKeySequence(Qt.Key_Space))
        except Exception:
            pass

        self._audio.setVolume(self.vol_slider.value() / 100.0)

    def set_source(self, path: Optional[str]) -> None:
        self._has_media = False
        if self._player is None or self._audio is None:
            return

        if not path or not os.path.exists(path):
            self._player.setSource(QUrl())
            self._show_placeholder("لا يوجد فيديو ملخص بعد.")
            self._set_controls_enabled(False)
            return

        abs_path = os.path.abspath(path)
        self._player.setSource(QUrl.fromLocalFile(abs_path))
        self._has_media = True
        self._show_video()
        self._set_controls_enabled(True)

    def _show_placeholder(self, text: str) -> None:
        if self._video is not None:
            self._video.hide()
        self.placeholder.setText(text)
        self.placeholder.show()

    def _show_video(self) -> None:
        self.placeholder.hide()
        if self._video is not None:
            self._video.show()

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.play_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(enabled)
        self.pos_slider.setEnabled(enabled)
        self.vol_btn.setEnabled(enabled)
        self.vol_slider.setEnabled(enabled)

    def play(self) -> None:
        if self._player is None or not self._has_media:
            return
        self._player.play()

    def pause(self) -> None:
        if self._player is None:
            return
        self._player.pause()

    def stop(self) -> None:
        if self._player is None:
            return
        self._player.stop()

    def _toggle_play_pause(self) -> None:
        if self._player is None:
            return
        state = self._player.playbackState()
        if state == self._player.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _toggle_mute(self) -> None:
        if self._audio is None:
            return
        self._audio.setMuted(not self._audio.isMuted())
        self.vol_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaVolumeMuted if self._audio.isMuted() else QStyle.SP_MediaVolume)
        )

    def _on_volume_changed(self, value: int) -> None:
        if self._audio is None:
            return
        self._audio.setVolume(max(0.0, min(1.0, value / 100.0)))

    @Slot(int)
    def _on_duration_changed(self, duration: int) -> None:
        self.pos_slider.setRange(0, max(0, int(duration)))
        self._update_time_label()

    @Slot(int)
    def _on_position_changed(self, position: int) -> None:
        if self._dragging:
            return
        self.pos_slider.setValue(int(position))
        self._update_time_label()

    @Slot()
    def _on_seek_start(self) -> None:
        self._dragging = True

    @Slot()
    def _on_seek_end(self) -> None:
        self._dragging = False
        if self._player is not None:
            self._player.setPosition(int(self.pos_slider.value()))
        self._update_time_label()

    @Slot(int)
    def _on_seek_move(self, _value: int) -> None:
        self._update_time_label(preview_ms=int(self.pos_slider.value()))

    def _update_time_label(self, preview_ms: Optional[int] = None) -> None:
        if self._player is None:
            return
        cur = int(preview_ms) if preview_ms is not None else int(self._player.position())
        total = int(self._player.duration())
        self.time_label.setText(f"{_format_time_ms(cur)} / {_format_time_ms(total)}")

    @Slot(object)
    def _on_state_changed(self, _state) -> None:
        if self._player is None:
            return
        state = self._player.playbackState()
        self.play_btn.setIcon(
            self.style().standardIcon(QStyle.SP_MediaPause if state == self._player.PlaybackState.PlayingState else QStyle.SP_MediaPlay)
        )

    @Slot(object, str)
    def _on_error(self, _err, msg: str) -> None:
        if msg:
            self._show_placeholder(f"تعذر تشغيل الفيديو.\n{msg}")


class VideoComparisonPanel(QFrame):
    """Summarized video playback + summarized properties."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setLayoutDirection(Qt.RightToLeft)
        apply_card_shadow(self)

        self._summary_path: Optional[str] = None
        self._result: Optional[dict] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title_row = QWidget(self)
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)

        icon = QLabel("🎬", title_row)
        icon.setStyleSheet("font-size: 18px;")
        title = QLabel("فيديو الملخص", title_row)
        title.setStyleSheet("font-size: 14px; font-weight: bold;")

        title_layout.addWidget(icon)
        title_layout.addWidget(title)
        title_layout.addStretch()

        self.toggle_props_btn = QPushButton("عرض الخصائص", title_row)
        self.toggle_props_btn.clicked.connect(self._toggle_properties)
        self.toggle_props_btn.setEnabled(False)
        title_layout.addWidget(self.toggle_props_btn)

        layout.addWidget(title_row)

        self.player = _MediaPlayerWidget(self)
        layout.addWidget(self.player, 1)

        self._props_group = self._build_properties_group()
        self._props_scroll = QScrollArea(self)
        self._props_scroll.setWidgetResizable(True)
        self._props_scroll.setFrameShape(QFrame.NoFrame)
        self._props_scroll.setWidget(self._props_group)
        self._props_scroll.setVisible(False)
        self._props_scroll.setMaximumHeight(260)
        layout.addWidget(self._props_scroll, 0)

    def _build_properties_group(self) -> QWidget:
        from PySide6.QtWidgets import QFormLayout, QGroupBox

        group = QGroupBox("خصائص الملخص", self)
        form = QFormLayout(group)
        form.setLabelAlignment(Qt.AlignRight)

        def val_label() -> QLabel:
            lab = QLabel("—", group)
            lab.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lab.setWordWrap(True)
            lab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return lab

        self._prop_video_name = val_label()
        self._prop_duration = val_label()
        self._prop_fps = val_label()
        self._prop_total_frames = val_label()
        self._prop_selected_frames = val_label()
        self._prop_reduced = val_label()
        self._prop_segments = val_label()
        self._prop_cached = val_label()
        self._prop_checksum = val_label()
        self._prop_output_dir = val_label()

        form.addRow("اسم الفيديو:", self._prop_video_name)
        form.addRow("المدة:", self._prop_duration)
        form.addRow("FPS:", self._prop_fps)
        form.addRow("عدد الإطارات:", self._prop_total_frames)
        form.addRow("الإطارات المختارة:", self._prop_selected_frames)
        form.addRow("تقليل الإطارات:", self._prop_reduced)
        form.addRow("عدد المقاطع:", self._prop_segments)
        form.addRow("الكاش:", self._prop_cached)
        form.addRow("Checksum:", self._prop_checksum)
        form.addRow("مجلد النتائج:", self._prop_output_dir)
        return group

    def set_summary(self, summary_path: Optional[str], result: Optional[dict]) -> None:
        prev = self._summary_path
        self._summary_path = summary_path if summary_path and os.path.exists(summary_path) else None
        self._result = result or None

        self.player.set_source(self._summary_path)
        self._refresh_properties()

        has_summary = bool(self._summary_path) and bool(self._result)
        self.toggle_props_btn.setEnabled(has_summary)
        if not has_summary:
            self._props_scroll.setVisible(False)
            self.toggle_props_btn.setText("عرض الخصائص")
            return

        if self._summary_path and self._summary_path != prev:
            self.player.play()

    def _refresh_properties(self) -> None:
        r = self._result or {}

        def _fmt_duration(sec) -> str:
            if isinstance(sec, (int, float)):
                return f"{sec:.2f} ثانية"
            return "—"

        def _fmt_float(x, suffix: str = "") -> str:
            if isinstance(x, (int, float)):
                return f"{float(x):.2f}{suffix}"
            return "—"

        self._prop_video_name.setText(str(r.get("video_name") or "—"))
        self._prop_duration.setText(_fmt_duration(r.get("duration_sec")))
        self._prop_fps.setText(_fmt_float(r.get("fps")))
        self._prop_total_frames.setText(str(r.get("total_frames") if r.get("total_frames") is not None else "—"))
        self._prop_selected_frames.setText(
            str(r.get("selected_frames_count") if r.get("selected_frames_count") is not None else "—")
        )
        self._prop_reduced.setText(_fmt_float(r.get("frames_reduced_pct"), "%"))
        self._prop_segments.setText(str(r.get("segments_count") if r.get("segments_count") is not None else "—"))
        self._prop_cached.setText("نعم" if r.get("cached") else "لا")
        checksum = r.get("checksum")
        self._prop_checksum.setText(str(checksum[:16] if isinstance(checksum, str) else "—"))
        self._prop_output_dir.setText(str(r.get("output_dir") or "—"))

    def _toggle_properties(self) -> None:
        visible = not self._props_scroll.isVisible()
        self._props_scroll.setVisible(visible)
        self.toggle_props_btn.setText("إخفاء الخصائص" if visible else "عرض الخصائص")

