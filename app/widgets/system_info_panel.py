# app/widgets/system_info_panel.py
from __future__ import annotations

import os
import platform
import time
from dataclasses import dataclass
from typing import Optional

import psutil
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass
class _SystemInfo:
    os_name: str
    cpu: str
    ram_total_gb: float
    torch_status: str
    cuda_status: str
    gpu_name: str
    vram_status: str


class _CudaBenchmarkThread(QThread):
    progress = Signal(str)
    result = Signal(dict)
    error = Signal(str)

    def __init__(self, video_path: Optional[str], parent=None):
        super().__init__(parent)
        self._video_path = video_path

    def run(self) -> None:  # noqa: C901
        try:
            import cv2  # type: ignore
        except Exception as exc:
            self.error.emit(f"OpenCV غير متاح: {exc}")
            return

        try:
            import torch  # type: ignore
        except Exception as exc:
            self.error.emit(f"PyTorch غير متاح: {exc}")
            return

        if not self._video_path or not os.path.exists(self._video_path):
            self.error.emit("يرجى اختيار فيديو أولاً لتشغيل اختبار CUDA.")
            return

        if not torch.cuda.is_available():
            self.error.emit("CUDA غير متاح على هذا الجهاز.")
            return

        device = torch.device("cuda:0")
        self.progress.emit("بدء اختبار CUDA…")

        cap = cv2.VideoCapture(self._video_path)
        if not cap.isOpened():
            self.error.emit("تعذر فتح الفيديو للاختبار.")
            return

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frames_target = int(min(total_frames, max(1, int((fps or 25.0) * 5.0))))

        self.progress.emit(f"قراءة أول 5 ثواني (~{frames_target} إطار)…")

        # Warm-up
        torch.cuda.synchronize()
        warm = torch.randn((256, 256), device=device, dtype=torch.float16)
        _ = warm @ warm
        torch.cuda.synchronize()

        mem_before = None
        try:
            mem_before = torch.cuda.mem_get_info()
        except Exception:
            mem_before = None

        start = time.perf_counter()
        processed = 0

        # Lightweight GPU workload per frame (keeps the test deterministic and fast).
        w = torch.randn((3, 3), device=device, dtype=torch.float16)

        while processed < frames_target:
            ok, frame = cap.read()
            if not ok:
                break

            # Frame -> tensor (downsample to keep it quick).
            small = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
            t = torch.from_numpy(small).to(device=device, dtype=torch.float16, non_blocking=False)

            # Simple math ops
            t = t * 0.992 + 0.008
            t = t[..., :3] if t.shape[-1] >= 3 else t
            t = t.mean(dim=2)  # (H,W)
            _ = (t[:3, :3].flatten() @ w.flatten())

            processed += 1
            if processed in {1, max(1, frames_target // 2), frames_target}:
                self.progress.emit(f"تقدم اختبار CUDA: {processed}/{frames_target} إطار")

        cap.release()
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start

        mem_after = None
        try:
            mem_after = torch.cuda.mem_get_info()
        except Exception:
            mem_after = None

        self.result.emit(
            {
                "video_path": os.path.abspath(self._video_path),
                "frames_target": frames_target,
                "frames_processed": processed,
                "elapsed_sec": round(elapsed, 4),
                "fps_input": fps,
                "cuda_version": getattr(torch.version, "cuda", None),
                "gpu_name": torch.cuda.get_device_name(0),
                "mem_before": mem_before,
                "mem_after": mem_after,
            }
        )


from ..theme import apply_card_shadow

class SystemInfoPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setLayoutDirection(Qt.RightToLeft)
        apply_card_shadow(self)

        self._video_path: Optional[str] = None
        self._torch = None
        self._torch_error: Optional[Exception] = None
        self._bench: Optional[_CudaBenchmarkThread] = None

        self._setup_ui()
        self.update_info()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        icon = QLabel("🧩", header)
        icon.setStyleSheet("font-size: 18px;")
        title = QLabel("معلومات النظام / CUDA", header)
        title.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.refresh_btn = QPushButton("تحديث", header)
        self.refresh_btn.clicked.connect(self.update_info)

        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        root.addWidget(header)

        self._selected_video_label = QLabel("الفيديو المحدد للاختبار: —", self)
        self._selected_video_label.setWordWrap(True)
        self._selected_video_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        root.addWidget(self._selected_video_label)

        # Scrollable sections container (prevents underlay when space is tight).
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)

        self._sections_host = QWidget(self._scroll)
        self._sections_layout = QVBoxLayout(self._sections_host)
        self._sections_layout.setContentsMargins(0, 0, 0, 0)
        self._sections_layout.setSpacing(10)
        self._scroll.setWidget(self._sections_host)
        root.addWidget(self._scroll, 1)

        self._sec_os = self._make_section("🖥️", "النظام", "—")
        self._sec_cpu = self._make_section("⚙️", "المعالج", "—")
        self._sec_ram = self._make_progress_section("🧠", "الذاكرة")
        self._sec_torch = self._make_section("🔥", "PyTorch", "—")
        self._sec_cuda = self._make_section("🟩", "CUDA", "—")
        self._sec_gpu = self._make_section("🎮", "GPU", "—")
        self._sec_vram = self._make_progress_section("📦", "VRAM")

        for sec in (
            self._sec_os,
            self._sec_cpu,
            self._sec_ram,
            self._sec_torch,
            self._sec_cuda,
            self._sec_gpu,
            self._sec_vram,
        ):
            self._sections_layout.addWidget(sec)

        self._sections_layout.addStretch()

        bench_row = QWidget(self)
        bench_layout = QHBoxLayout(bench_row)
        bench_layout.setContentsMargins(0, 0, 0, 0)
        bench_layout.setSpacing(8)

        self.cuda_button = QPushButton("تشغيل اختبار CUDA", bench_row)
        self.cuda_button.setObjectName("primary_btn")
        self.cuda_button.clicked.connect(self.run_cuda_benchmark)

        bench_layout.addWidget(self.cuda_button)
        bench_layout.addStretch()
        root.addWidget(bench_row)

        self.bench_log = QTextEdit(self)
        self.bench_log.setReadOnly(True)
        self.bench_log.setMinimumHeight(140)
        self.bench_log.setPlaceholderText("سجل اختبار CUDA سيظهر هنا…")
        root.addWidget(self.bench_log, 0)

    def _make_section(self, icon: str, title: str, value: str) -> QFrame:
        sec = QFrame(self)
        sec.setObjectName("info_section")
        sec.setLayoutDirection(Qt.RightToLeft)

        row = QHBoxLayout(sec)
        row.setContentsMargins(10, 10, 10, 10)
        row.setSpacing(10)

        icon_label = QLabel(icon, sec)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setMinimumWidth(34)
        icon_label.setStyleSheet("font-size: 18px;")

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        title_label = QLabel(title, sec)
        title_label.setStyleSheet("font-weight: bold;")
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        value_label = QLabel(value, sec)
        value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_label.setWordWrap(True)
        value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        text_col.addWidget(title_label)
        text_col.addWidget(value_label)

        row.addWidget(icon_label, 0)
        row.addLayout(text_col, 1)

        sec._value_label = value_label  # type: ignore[attr-defined]
        return sec

    def _make_progress_section(self, icon: str, title: str) -> QFrame:
        from PySide6.QtWidgets import QProgressBar
        sec = QFrame(self)
        sec.setObjectName("info_section")
        sec.setLayoutDirection(Qt.RightToLeft)

        row = QHBoxLayout(sec)
        row.setContentsMargins(10, 10, 10, 10)
        row.setSpacing(10)

        icon_label = QLabel(icon, sec)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setMinimumWidth(34)
        icon_label.setStyleSheet("font-size: 18px;")

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        title_label = QLabel(title, sec)
        title_label.setStyleSheet("font-weight: bold;")
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        pb = QProgressBar(sec)
        pb.setRange(0, 100)
        pb.setValue(0)
        pb.setTextVisible(True)

        text_col.addWidget(title_label)
        text_col.addWidget(pb)

        row.addWidget(icon_label, 0)
        row.addLayout(text_col, 1)

        sec._value_label = pb  # type: ignore[attr-defined]
        return sec

    def _set_section_value(self, section: QFrame, value: str) -> None:
        lab = getattr(section, "_value_label", None)
        if isinstance(lab, QLabel):
            lab.setText(value)

    def _set_progress_value(self, section: QFrame, percent: int, text: str) -> None:
        from PySide6.QtWidgets import QProgressBar
        pb = getattr(section, "_value_label", None)
        if isinstance(pb, QProgressBar):
            pb.setValue(percent)
            pb.setFormat(text)

    def set_video_path(self, path: Optional[str]) -> None:
        self._video_path = path if path and os.path.exists(path) else None
        self._selected_video_label.setText(
            f"الفيديو المحدد للاختبار: {os.path.basename(self._video_path) if self._video_path else '—'}"
        )

    def _get_torch(self):
        if self._torch is not None or self._torch_error is not None:
            return self._torch
        try:
            import torch  # type: ignore
        except Exception as exc:
            self._torch_error = exc
            self._torch = None
        else:
            self._torch = torch
            self._torch_error = None
        return self._torch

    @Slot()
    def update_info(self) -> None:
        info = _SystemInfo(
            os_name=f"{platform.system()} {platform.release()}",
            cpu=platform.processor() or "—",
            ram_total_gb=float(psutil.virtual_memory().total) / (1024**3),
            torch_status="—",
            cuda_status="—",
            gpu_name="—",
            vram_status="—",
        )

        torch = self._get_torch()
        if torch is None:
            info.torch_status = "غير متاح"
            if self._torch_error is not None:
                info.torch_status = f"غير متاح ({self._torch_error})"
            info.cuda_status = "غير معروف"
            self.cuda_button.setEnabled(False)
        else:
            info.torch_status = getattr(torch, "__version__", "متاح")
            if torch.cuda.is_available():
                self.cuda_button.setEnabled(self._bench is None)
                info.cuda_status = str(getattr(torch.version, "cuda", "متاح"))
                try:
                    info.gpu_name = torch.cuda.get_device_name(0)
                except Exception:
                    info.gpu_name = "—"
                try:
                    free_b, total_b = torch.cuda.mem_get_info()
                    used_b = total_b - free_b
                    vram_pct = int((used_b / total_b) * 100)
                    self._set_progress_value(self._sec_vram, vram_pct, f"{used_b/(1024**3):.1f} GB / {total_b/(1024**3):.1f} GB")
                except Exception:
                    self._set_progress_value(self._sec_vram, 0, "—")
            else:
                self.cuda_button.setEnabled(False)
                info.cuda_status = "غير متاح"
                self._set_progress_value(self._sec_vram, 0, "—")

        self._set_section_value(self._sec_os, info.os_name)
        self._set_section_value(self._sec_cpu, info.cpu)
        
        ram_vm = psutil.virtual_memory()
        self._set_progress_value(self._sec_ram, int(ram_vm.percent), f"{ram_vm.used / (1024**3):.1f} GB / {ram_vm.total / (1024**3):.1f} GB")
        
        self._set_section_value(self._sec_torch, info.torch_status)
        self._set_section_value(self._sec_cuda, info.cuda_status)
        self._set_section_value(self._sec_gpu, info.gpu_name)

    @Slot()
    def run_cuda_benchmark(self) -> None:
        if self._bench is not None:
            return

        torch = self._get_torch()
        if torch is None or not getattr(torch, "cuda", None) or not torch.cuda.is_available():
            self.bench_log.append("CUDA غير متاح. تحقق من تثبيت PyTorch + CUDA.")
            self.cuda_button.setEnabled(False)
            return

        self.cuda_button.setEnabled(False)
        self.cuda_button.setText("جاري الاختبار…")
        self.bench_log.append("بدء اختبار CUDA…")

        self._bench = _CudaBenchmarkThread(self._video_path, self)
        self._bench.progress.connect(self._on_bench_progress)
        self._bench.result.connect(self._on_bench_result)
        self._bench.error.connect(self._on_bench_error)
        self._bench.finished.connect(self._on_bench_finished)
        self._bench.start()

    @Slot(str)
    def _on_bench_progress(self, msg: str) -> None:
        self.bench_log.append(msg)

    @Slot(dict)
    def _on_bench_result(self, res: dict) -> None:
        self.bench_log.append("—" * 18)
        self.bench_log.append(f"الفيديو: {res.get('video_path')}")
        self.bench_log.append(f"المعالجة: {res.get('frames_processed')}/{res.get('frames_target')} إطار")
        self.bench_log.append(f"الزمن: {res.get('elapsed_sec')} ثانية")
        self.bench_log.append(f"GPU: {res.get('gpu_name')}")
        self.bench_log.append(f"CUDA: {res.get('cuda_version')}")
        mem_after = res.get("mem_after")
        if isinstance(mem_after, (list, tuple)) and len(mem_after) == 2:
            free_b, total_b = mem_after
            self.bench_log.append(f"VRAM بعد الاختبار: {free_b/(1024**3):.1f} GB free / {total_b/(1024**3):.1f} GB total")
        self.bench_log.append("—" * 18)

    @Slot(str)
    def _on_bench_error(self, err: str) -> None:
        self.bench_log.append(f"[ERROR] {err}")

    @Slot()
    def _on_bench_finished(self) -> None:
        self._bench = None
        self.cuda_button.setText("تشغيل اختبار CUDA")
        self.update_info()
        # update_info() decides whether the button should be enabled.
