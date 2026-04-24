# -*- coding: utf-8 -*-
"""Main entry point for PySide6 UI."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.ui_pyside6.main_window import MainWindow
from app.ui_pyside6.fonts import load_app_fonts, get_app_font


def main():
    try:
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except ImportError:
        pass
    
    app = QApplication(sys.argv)

    load_app_fonts()
    
    font = get_app_font("Regular", 10)
    font.setStyleHint(QFont.StyleHint.Monospace)
    app.setFont(font)
    
    app.setApplicationName("تحليل لقطات المراقبة")
    app.setOrganizationName("CCTV")
    app.setApplicationDisplayName("CCTV Footage Analyzer")
    
    app.setLayoutDirection(Qt.RightToLeft)
    
    try:
        from PySide6.QtWinExtras import QtWin
        QtWin.enableBlurBehindWindow(app)
    except ImportError:
        pass
    
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    main()