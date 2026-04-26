# app/dialogs/dialog_factory.py
from PySide6.QtWidgets import QMessageBox, QFileDialog, QInputDialog
from PySide6.QtCore import Qt

def _create_msg_box(parent, title, message, icon):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(message)
    box.setIcon(icon)
    box.setLayoutDirection(Qt.RightToLeft)
    return box

def show_info(parent, title, message):
    box = _create_msg_box(parent, title, message, QMessageBox.Information)
    box.setStandardButtons(QMessageBox.Ok)
    box.exec()

def show_warning(parent, title, message):
    box = _create_msg_box(parent, title, message, QMessageBox.Warning)
    box.setStandardButtons(QMessageBox.Ok)
    box.exec()

def show_error(parent, title, message):
    box = _create_msg_box(parent, title, message, QMessageBox.Critical)
    box.setStandardButtons(QMessageBox.Ok)
    box.exec()

def show_confirm(parent, title, message):
    box = _create_msg_box(parent, title, message, QMessageBox.Question)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    return box.exec() == QMessageBox.Yes

def show_file_open(parent, filter="All Files (*)"):
    file_path, _ = QFileDialog.getOpenFileName(parent, "Select Video File", "", filter)
    return file_path

def show_file_save(parent, filter="MP4 Files (*.mp4)", default=""):
    file_path, _ = QFileDialog.getSaveFileName(parent, "Save Video", default, filter)
    return file_path