from __future__ import annotations

import sys
import threading
import traceback
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget

from .dialogs.unhandled_exception_dialog import UnhandledExceptionDialog
from .theme import get_theme_manager


class _ExceptionDispatcher(QObject):
    exception_captured = Signal(str)  # traceback text

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._handling = False
        self.exception_captured.connect(self._show_dialog)

    @Slot(str)
    def _show_dialog(self, traceback_text: str):
        if self._handling:
            return

        self._handling = True
        try:
            app = QApplication.instance()
            parent = app.activeWindow() if app else None
            dialog = UnhandledExceptionDialog(traceback_text, parent=parent)
            dialog.setStyleSheet(get_theme_manager().get_stylesheet())
            dialog.exec()

            if dialog.choice == UnhandledExceptionDialog.ExitChoice and app is not None:
                app.exit(1)
        finally:
            self._handling = False


_dispatcher: Optional[_ExceptionDispatcher] = None


def _format_traceback(exc_type, exc_value, exc_tb) -> str:
    return "".join(traceback.format_exception(exc_type, exc_value, exc_tb))


def install_exception_handling() -> None:
    """Install global hooks to catch otherwise-unhandled exceptions.

    Shows a custom dialog with traceback and lets the user Continue or Exit.
    Must be called after creating a `QApplication`.
    """
    global _dispatcher

    app = QApplication.instance()
    if app is None:
        raise RuntimeError("install_exception_handling() must be called after QApplication is created")

    if _dispatcher is None:
        _dispatcher = _ExceptionDispatcher(parent=app)

    def sys_excepthook(exc_type, exc_value, exc_tb):
        trace = _format_traceback(exc_type, exc_value, exc_tb)
        try:
            _dispatcher.exception_captured.emit(trace)  # type: ignore[union-attr]
        except Exception:
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = sys_excepthook

    if hasattr(threading, "excepthook"):
        def thread_excepthook(args):
            trace = _format_traceback(args.exc_type, args.exc_value, args.exc_traceback)
            try:
                _dispatcher.exception_captured.emit(trace)  # type: ignore[union-attr]
            except Exception:
                sys.__excepthook__(args.exc_type, args.exc_value, args.exc_traceback)

        threading.excepthook = thread_excepthook  # type: ignore[attr-defined]


class ExceptionHandlingApplication(QApplication):
    """QApplication that catches exceptions raised during Qt event dispatch.

    This is the only place where "Continue (ignore)" is reliably possible for
    UI-driven exceptions, since `sys.excepthook` is fatal for the main thread.
    """

    def notify(self, receiver, event):  # type: ignore[override]
        try:
            return super().notify(receiver, event)
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            trace = _format_traceback(exc_type, exc_value, exc_tb)

            app = QApplication.instance()
            if app is None:
                raise

            if _dispatcher is None:
                # Best-effort fallback.
                raise

            _dispatcher.exception_captured.emit(trace)

            # If user chose Exit, the dispatcher already called app.exit(1).
            # Returning False ignores the current event and keeps the app alive.
            return False


def show_startup_exception(traceback_text: str) -> int:
    """Handle an exception during startup and return an exit code.

    Returns 0 to continue running (with a minimal fallback window), or 1 to exit.
    """
    app = QApplication.instance()
    if app is None:
        return 1

    dispatcher = _dispatcher or _ExceptionDispatcher(parent=app)
    if _dispatcher is None:
        # Keep singleton updated if install_exception_handling() wasn't called.
        globals()["_dispatcher"] = dispatcher

    dialog = UnhandledExceptionDialog(traceback_text, parent=app.activeWindow())
    dialog.setStyleSheet(get_theme_manager().get_stylesheet())
    dialog.exec()

    if dialog.choice == UnhandledExceptionDialog.ExitChoice:
        return 1

    # Continue: keep the instance alive with a simple error window.
    win = QMainWindow()
    win.setWindowTitle("تم بدء التطبيق مع خطأ")
    central = QWidget(win)
    layout = QVBoxLayout(central)
    text = QTextEdit(central)
    text.setReadOnly(True)
    text.setPlainText(traceback_text)
    text.setLayoutDirection(Qt.LeftToRight)
    layout.addWidget(text)
    win.setCentralWidget(central)
    win.resize(900, 600)
    win.setStyleSheet(get_theme_manager().get_stylesheet())
    win.show()
    setattr(app, "_startup_error_window", win)

    return 0
