# app/state/application_state.py
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication
import json
import os

class ApplicationState(QObject):
    # Signals
    processing_changed = Signal(bool)
    result_changed = Signal(dict)
    error_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_processing = False
        self._result = {}
        self._error = ""

    @property
    def is_processing(self):
        return self._is_processing

    @is_processing.setter
    def is_processing(self, value):
        if self._is_processing != value:
            self._is_processing = value
            self.processing_changed.emit(value)

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        self._result = value
        self.result_changed.emit(value)

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, value):
        self._error = value
        self.error_changed.emit(value)

# Singleton
app_state = ApplicationState()
