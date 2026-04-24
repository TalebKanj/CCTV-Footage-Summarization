"""Syrian-inspired theme manager for PySide6."""

from typing import Dict
from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):
    """Manages dark/light theme switching with Syrian-inspired colors."""

    theme_changed = Signal(str)

    SYRIAN_THEME = {
    "dark": {
        "background": "#161616",      # Charcoal (الأسود الفحمي للخلفية الأساسية)
        "card_bg": "#002623",          # Forest Dark (الأخضر الغامق للبطاقات)
        "surface": "#054239",         # Forest Medium (الأسطح الفرعية)
        "primary": "#b9a779",         # Golden Wheat (الذهبي كلون أساسي للهوية)
        "primary_hover": "#988561",    # Golden Wheat Dark (عند التمرير)
        "text_primary": "#edebe0",     # Light Wheat (نص فاتح مريح للعين)
        "text_secondary": "#428177",   # Forest Muted (نص ثانوي بلون غابة خافت)
        "border": "#988561",           # Golden Wheat (الحدود باللون الذهبي)
        "cta_button": "#6b1f2a",       # Deep Umber (الأحمر العميق لأزرار اتخاذ الإجراء)
        "cta_hover": "#4a151e",        # Deep Umber Dark (عند التمرير على الأزرار)
    },
    "light": {
        "background": "#edebe0",       # Light Wheat (خلفية فاتحة من درجات القمح)
        "card_bg": "#ffffff",          # White (البطاقات باللون الأبيض النقي)
        "surface": "#f8f9fa",          # Light Grey Surface
        "primary": "#002623",          # Forest Dark (الأخضر الغامق كلون أساسي في الوضع الفاتح)
        "primary_hover": "#054239",    
        "text_primary": "#161616",     # Charcoal (نص أساسي غامق)
        "text_secondary": "#3d3a3b",   # Charcoal Medium (نص ثانوي)
        "border": "#b9a779",           # Golden Wheat (الحدود بالذهبي)
        "cta_button": "#6b1f2a",       # Deep Umber (الأحمر العميق للأزرار)
        "cta_hover": "#4a151e",
    }
}

    def __init__(self, parent=None):
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
    background-color: {t["background"]};
    color: {t["text_primary"]};
}}

QPushButton {{
    background: linear-gradient(135deg, {t["primary"]} 0%, {t["primary_hover"]} 100%);
    color: {t["background"]};
    border: none;
    border-radius: 7px;
    padding: 8px 16px;
    font-weight: bold;
    min-height: 32px;
}}

QPushButton:hover {{
    background: {t["primary"]};
}}

QPushButton:pressed {{
    background: {t["primary_hover"]};
}}

QPushButton#process_btn {{
    background: linear-gradient(135deg, {t["cta_button"]} 0%, {t["cta_hover"]} 100%);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: bold;
    font-size: 14px;
    min-height: 40px;
    min-width: 160px;
}}

QPushButton#process_btn:hover {{
    background: linear-gradient(135deg, {t["cta_hover"]} 0%, {t["cta_button"]} 100%);
}}

QPushButton#process_btn:disabled {{
    background: {t["surface"]};
    color: {t["text_secondary"]};
    min-height: 40px;
    min-width: 160px;
}}

QPushButton#process_btn:pressed {{
    background: {t["surface"]};
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

QLabel {{
    color: {t["text_primary"]};
}}

QFrame#card {{
    background-color: {t["card_bg"]};
    border: 1px solid {t["border"]};
    border-radius: 12px;
    padding: 16px;
}}

QFrame#drop_zone {{
    background-color: {t["surface"]};
    border: 2px dashed {t["border"]};
    border-radius: 10px;
    min-height: 150px;
    padding: 24px;
}}

QFrame#drop_zone:hover {{
    border-color: {t["primary"]};
    background-color: {t["card_bg"]};
}}

QFrame#header {{
    background-color: {t["card_bg"]};
    border-bottom: 1px solid {t["border"]};
}}

QStatusBar {{
    background-color: {t["card_bg"]};
    color: {t["text_secondary"]};
    border-top: 1px solid {t["border"]};
}}

QDialog {{
    background-color: {t["background"]};
}}

QComboBox {{
    background-color: {t["surface"]};
    color: {t["text_primary"]};
    border: 1px solid {t["border"]};
    border-radius: 5px;
    padding: 5px;
    min-height: 28px;
}}

QLineEdit {{
    background-color: {t["surface"]};
    color: {t["text_primary"]};
    border: 1px solid {t["border"]};
    border-radius: 5px;
    padding: 5px;
}}

QSlider::groove:horizontal {{
    background-color: {t["surface"]};
    border-radius: 3px;
    min-height: 6px;
}}

QSlider::handle:horizontal {{
    background-color: {t["primary"]};
    border-radius: 8px;
    min-width: 16px;
    min-height: 16px;
}}

QSlider::add-page:horizontal {{
    background-color: {t["surface"]};
}}

QSlider::sub-page:horizontal {{
    background: linear-gradient(90deg, {t["primary"]} 0%, {t["primary_hover"]} 100%);
}}
"""

    def toggle_theme(self):
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self.theme_changed.emit(self._current_theme)

    def set_theme(self, theme: str):
        if theme in self.SYRIAN_THEME:
            self._current_theme = theme
            self.theme_changed.emit(self._current_theme)


_theme_manager_instance = None


def get_theme_manager() -> ThemeManager:
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = ThemeManager()
    return _theme_manager_instance