"""Custom font loader for PySide6 UI."""

import os
from PySide6.QtGui import QFont, QFontDatabase


ARABIC_FONT_FAMILY = "Itf Qomra Arabic"
FALLBACK_FONTS = ["Traditional Arabic", "Arial", "Tahoma", "Segoe UI", "DejaVu Sans"]


def load_app_fonts():
    """Load custom Arabic fonts from assets directory."""
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assets_dir = os.path.join(app_dir, "assets")
    loaded_fonts = []

    if not os.path.exists(assets_dir):
        return loaded_fonts

    font_weights = ["Regular", "Bold", "Medium", "Light"]

    for weight in font_weights:
        font_path = os.path.join(assets_dir, f"itfQomraArabic-{weight}.otf")
        if os.path.exists(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if ARABIC_FONT_FAMILY not in loaded_fonts:
                    loaded_fonts.append(ARABIC_FONT_FAMILY)
                loaded_fonts.extend(families)

    return loaded_fonts


def _get_font_family() -> str:
    """Get the best available font family, with fallback."""
    available_families = QFontDatabase.families()
    
    if ARABIC_FONT_FAMILY in available_families:
        return ARABIC_FONT_FAMILY
    
    for font in FALLBACK_FONTS:
        if font in available_families:
            return font
    
    return ""


def get_app_font(weight: str = "Regular", size: int = 12) -> QFont:
    """Get a QFont instance with the custom Arabic font."""
    font_family = _get_font_family()
    
    if font_family:
        font = QFont(font_family, size)
    else:
        font = QFont(size)
        font.setStyleHint(QFont.StyleHint.System)
    
    weight_map = {
        "Light": QFont.Weight.Light,
        "Regular": QFont.Weight.Normal,
        "Medium": QFont.Weight.Medium,
        "Bold": QFont.Weight.Bold,
    }

    if weight in weight_map:
        font.setWeight(weight_map[weight])

    return font


def apply_font_to_widget(widget, weight: str = "Regular", size: int = 12):
    """Apply the custom Arabic font to a widget."""
    font = get_app_font(weight, size)
    widget.setFont(font)