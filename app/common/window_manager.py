from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

window: QWidget | None


def set_window(new_window: QWidget) -> None:
    global window
    window = new_window

def get_window() -> QWidget | None:
    return window