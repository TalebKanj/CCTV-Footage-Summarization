"""Custom Arabic font loader for the PySide6 UI.

Keeps the `app/` UI Arabic-first while gracefully falling back to system fonts.
"""

from __future__ import annotations

import os

from PySide6.QtGui import QFont, QFontDatabase


ARABIC_FONT_FAMILY = "Itf Qomra Arabic"
FALLBACK_FONTS = ["Traditional Arabic", "Arial", "Tahoma", "Segoe UI", "DejaVu Sans"]


def load_app_fonts() -> list[str]:
    """Load bundled fonts from the repo `assets/` directory."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(repo_root, "assets")
    loaded_families: list[str] = []

    if not os.path.exists(assets_dir):
        return loaded_families

    for weight in ["Regular", "Bold", "Medium", "Light"]:
        font_path = os.path.join(assets_dir, f"itfQomraArabic-{weight}.otf")
        if not os.path.exists(font_path):
            continue

        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            continue

        families = QFontDatabase.applicationFontFamilies(font_id)
        loaded_families.extend(families)

    return loaded_families


def _get_font_family() -> str:
    available = set(QFontDatabase.families())
    if ARABIC_FONT_FAMILY in available:
        return ARABIC_FONT_FAMILY
    for font in FALLBACK_FONTS:
        if font in available:
            return font
    return ""


def get_app_font(weight: str = "Regular", size: int = 11) -> QFont:
    family = _get_font_family()
    font = QFont(family, size) if family else QFont(size)

    weight_map = {
        "Light": QFont.Weight.Light,
        "Regular": QFont.Weight.Normal,
        "Medium": QFont.Weight.Medium,
        "Bold": QFont.Weight.Bold,
    }
    if weight in weight_map:
        font.setWeight(weight_map[weight])

    return font

