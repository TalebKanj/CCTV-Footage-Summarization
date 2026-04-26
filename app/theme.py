"""Syrian-inspired theme manager for the PySide6 UI.

Ported from `app_oldUI` so `app/` can share the same visual scheme while keeping
the current `app/` architecture intact.
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):
    """Manages dark/light theme switching with Syrian-inspired colors."""

    theme_changed = Signal(str)

    SYRIAN_THEME: Dict[str, Dict[str, str]] = {
        "dark": {
            "background": "#161616",
            "background2": "#0f0f12",
            "card_bg": "#002623",
            "card_bg2": "#01352f",
            "surface": "#054239",
            "surface2": "#073f37",
            "primary": "#b9a779",
            "primary_hover": "#988561",
            "primary_soft": "#cbbd94",
            "text_primary": "#edebe0",
            "text_secondary": "#428177",
            "border": "#988561",
            "cta_button": "#6b1f2a",
            "cta_hover": "#4a151e",
            "danger": "#CE1126",
            "shadow": "rgba(0,0,0,0.35)",
        },
        "light": {
            "background": "#edebe0",
            "background2": "#e2dfd2",
            "card_bg": "#ffffff",
            "card_bg2": "#f7f7f7",
            "surface": "#f8f9fa",
            "surface2": "#eef1f4",
            "primary": "#002623",
            "primary_hover": "#054239",
            "primary_soft": "#0b5b51",
            "text_primary": "#161616",
            "text_secondary": "#3d3a3b",
            "border": "#b9a779",
            "cta_button": "#6b1f2a",
            "cta_hover": "#4a151e",
            "danger": "#CE1126",
            "shadow": "rgba(0,0,0,0.12)",
        },
    }

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current_theme = "dark"

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def colors(self) -> Dict[str, str]:
        return self.SYRIAN_THEME.get(self._current_theme, self.SYRIAN_THEME["dark"])

    def get_stylesheet(self) -> str:
        t = self.colors
        return f"""
QMainWindow, QWidget {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {t["background2"]},
                                stop:1 {t["background"]});
    color: {t["text_primary"]};
    font-family: 'Cairo', 'Segoe UI', Arial, sans-serif;
}}

QFrame#card, QWidget#card {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {t["card_bg2"]},
                                stop:1 {t["card_bg"]});
    border: 1px solid rgba(185, 167, 121, 0.55);
    border-radius: 18px;
    padding: 12px;
}}

QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {t["primary_soft"]},
                                stop:1 {t["primary_hover"]});
    color: {t["background"]};
    border: 1px solid rgba(185, 167, 121, 0.35);
    border-radius: 14px;
    padding: 10px 16px;
    font-weight: bold;
    min-height: 32px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {t["primary"]},
                                stop:1 {t["primary_hover"]});
}}

QPushButton:pressed {{
    background: {t["primary_hover"]};
}}

QPushButton#primary_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {t["cta_button"]},
                                stop:1 {t["cta_hover"]});
    color: #ffffff;
    border-radius: 16px;
    padding: 12px 22px;
    min-height: 40px;
}}

QPushButton#primary_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {t["cta_hover"]},
                                stop:1 {t["cta_button"]});
}}

QPushButton#danger_btn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {t["surface2"]},
                                stop:1 {t["surface"]});
    color: {t["text_primary"]};
    border: 1px solid rgba(185, 167, 121, 0.35);
    border-radius: 14px;
    padding: 10px 16px;
    font-weight: bold;
    min-height: 32px;
}}

QPushButton#danger_btn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 {t["surface"]},
                                stop:1 {t["primary_hover"]});
}}

QPushButton:disabled {{
    background: {t["surface"]};
    color: {t["text_secondary"]};
    border: 1px solid rgba(185, 167, 121, 0.15);
}}

QProgressBar {{
    border: 1px solid {t["border"]};
    border-radius: 5px;
    text-align: center;
    background-color: {t["surface"]};
    min-height: 20px;
}}

QProgressBar::chunk {{
    background: linear-gradient(90deg, {t["primary"]} 0%, {t["primary_hover"]} 100%);
    border-radius: 4px;
}}

QTabWidget::pane {{
    border: none;
    background: transparent;
}}

QTabBar::tab {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {t["surface2"]},
                                stop:1 {t["surface"]});
    color: {t["text_secondary"]};
    border: 1px solid rgba(185, 167, 121, 0.35);
    padding: 8px 16px;
    margin: 2px;
    border-radius: 12px;
}}

QTabBar::tab:selected {{
    background-color: {t["card_bg"]};
    color: {t["text_primary"]};
    border-bottom: 2px solid {t["primary"]};
}}

QTabBar::tab:hover:!selected {{
    background-color: {t["primary"]};
    color: {t["background"]};
}}

QLineEdit, QTextEdit {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {t["surface2"]},
                                stop:1 {t["surface"]});
    color: {t["text_primary"]};
    border: 1px solid rgba(185, 167, 121, 0.30);
    border-radius: 12px;
    padding: 6px 8px;
}}

QSpinBox, QDoubleSpinBox, QComboBox {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {t["surface2"]},
                                stop:1 {t["surface"]});
    color: {t["text_primary"]};
    border: 1px solid rgba(185, 167, 121, 0.30);
    border-radius: 12px;
    padding: 6px 8px;
    min-height: 30px;
}}

QComboBox::drop-down {{
    border: none;
    width: 26px;
}}

QComboBox QAbstractItemView {{
    background: {t["card_bg"]};
    border: 1px solid rgba(185, 167, 121, 0.35);
    border-radius: 12px;
    selection-background-color: {t["primary"]};
    selection-color: {t["background"]};
}}

QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 1px solid rgba(185, 167, 121, 0.45);
    background: rgba(0, 0, 0, 0.10);
}}

QCheckBox::indicator:checked {{
    background: {t["primary"]};
    border: 1px solid rgba(185, 167, 121, 0.65);
}}

QTableWidget {{
    background: {t["card_bg"]};
    color: {t["text_primary"]};
    gridline-color: rgba(185, 167, 121, 0.30);
    border: 1px solid rgba(185, 167, 121, 0.35);
    border-radius: 14px;
}}

QTableWidget::item {{
    padding: 6px 8px;
    border-radius: 8px;
}}

QScrollArea, QAbstractScrollArea {{
    border: none;
    background: transparent;
}}

QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 {t["surface2"]},
                                stop:1 {t["surface"]});
    color: {t["text_primary"]};
    border: 1px solid rgba(185, 167, 121, 0.35);
    padding: 6px 8px;
}}

QGroupBox {{
    border: 1px solid rgba(185, 167, 121, 0.25);
    border-radius: 16px;
    margin-top: 10px;
    padding: 12px;
    background: rgba(0, 0, 0, 0.10);
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 8px;
    color: {t["primary"]};
    font-weight: bold;
}}

QSplitter::handle {{
    background: rgba(185, 167, 121, 0.12);
    border-radius: 6px;
}}

QLabel#video_view {{
    border: 1px solid rgba(185, 167, 121, 0.25);
    border-radius: 16px;
    background: rgba(0, 0, 0, 0.18);
}}

QFrame#info_section {{
    background: rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(185, 167, 121, 0.22);
    border-radius: 16px;
    padding: 10px;
}}

QScrollBar:vertical {{
    background: {t["surface"]};
    width: 12px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {t["primary_hover"]};
    min-height: 20px;
    border-radius: 6px;
}}
"""

    def toggle_theme(self) -> None:
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self.theme_changed.emit(self._current_theme)

    def set_theme(self, theme: str) -> None:
        if theme in self.SYRIAN_THEME:
            self._current_theme = theme
            self.theme_changed.emit(self._current_theme)


_theme_manager_instance: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = ThemeManager()
    return _theme_manager_instance

def apply_card_shadow(widget: QWidget) -> None:
    from PySide6.QtWidgets import QGraphicsDropShadowEffect
    from PySide6.QtGui import QColor
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(15)
    shadow.setYOffset(4)
    shadow.setXOffset(0)
    shadow.setColor(QColor(0, 0, 0, 80))
    widget.setGraphicsEffect(shadow)
