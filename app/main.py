# app/main.py
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from .fonts import load_app_fonts, get_app_font
from .theme import get_theme_manager
from .exceptions import ExceptionHandlingApplication, install_exception_handling, show_startup_exception

def main():
    try:
        from PySide6.QtGui import QGuiApplication

        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = ExceptionHandlingApplication(sys.argv)
    app.setStyle("Fusion")

    load_app_fonts()
    app.setFont(get_app_font("Regular", 10))

    app.setApplicationName("تحليل لقطات المراقبة")
    app.setOrganizationName("CCTV")
    app.setApplicationDisplayName("CCTV Footage Analyzer")
    app.setLayoutDirection(Qt.RightToLeft)

    import os
    from PySide6.QtGui import QIcon
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(repo_root, "assets", "logo_128.svg")
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    theme_manager = get_theme_manager()
    app.setStyleSheet(theme_manager.get_stylesheet())
    install_exception_handling()

    try:
        from .main_window import MainWindow

        window = MainWindow()
        window.show()
    except Exception:
        import traceback as _traceback

        tb = _traceback.format_exc()
        exit_code = show_startup_exception(tb)
        if exit_code != 0:
            sys.exit(exit_code)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
