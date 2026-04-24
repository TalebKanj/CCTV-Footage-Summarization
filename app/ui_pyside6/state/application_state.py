"""Application state singleton for PySide6 UI."""

from PySide6.QtCore import QObject, Signal


class ApplicationState(QObject):
    """Singleton application state manager."""
    
    _instance = None
    
    video_selected = Signal(str)
    processing_started = Signal()
    processing_finished = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._video_path = None
        self._result = None
        self._is_processing = False
        self._processing_result_emitted = False
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def video_path(self):
        return self._video_path
    
    @video_path.setter
    def video_path(self, path: str):
        self._video_path = path
        self.video_selected.emit(path)
    
    @property
    def result(self):
        return self._result
    
    @result.setter
    def result(self, result: dict):
        self._result = result
        if not self._processing_result_emitted:
            self._processing_result_emitted = True
            self.processing_finished.emit(result)
    
    @property
    def is_processing(self):
        return self._is_processing
    
    @is_processing.setter
    def is_processing(self, value: bool):
        self._is_processing = value
        if value:
            self._processing_result_emitted = False
            self.processing_started.emit()
    
    def reset(self):
        self._video_path = None
        self._result = None
        self._is_processing = False
        self._processing_result_emitted = False


app_state = ApplicationState.get_instance()
