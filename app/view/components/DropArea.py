import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QFileDialog
from qfluentwidgets import FluentIcon as FIF, TransparentToolButton

from app.common.style_sheet import DropStyleSheet
from app.common.utils import notify_util


class DropArea(QLabel):
    def __init__(self, parent, label):
        super().__init__(label, parent)
        self.setText(label)
        self.setWordWrap(True)
        self.parent_widget = parent
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.folderPath = ""

        self.delete_button = TransparentToolButton(self)
        self.delete_button.setFixedSize(20, 20)
        self.delete_button.setIcon(FIF.DELETE)
        self.delete_button.clicked.connect(self.clear)
        self.delete_button.hide()
        DropStyleSheet.WINDOW.apply(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.delete_button.move(self.width() - self.delete_button.width() - 10, 10)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile() and os.path.isdir(urls[0].toLocalFile()):
                event.acceptProposedAction()
            else:
                event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()

        if len(urls) == 1 and urls[0].isLocalFile():
            folder_path = urls[0].toLocalFile()
            if os.path.isdir(folder_path):
                self.folderPath = os.path.abspath(folder_path)
                folder_name = os.path.basename(self.folderPath)
                display_text = f"<b>{folder_name}</b><br><br>{self.folderPath}"
                self.setText(display_text)
                # self.setToolTip(self.folderPath)
                self.setAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Align text to the left and top
                self.delete_button.show()
            else:
                notify_util.notify_error(NotADirectoryError("Please drop a folder"), "")
        else:
            notify_util.notify_error(ValueError("Please drop only one folder"), "")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            folderPath = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folderPath:
                self.folderPath = os.path.abspath(folderPath)
                folder_name = os.path.basename(self.folderPath)
                display_text = f"<b>{folder_name}</b><br><br>{self.folderPath}"
                self.setText(display_text)
                # self.setToolTip(self.folderPath)
                self.setAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Align text to the left and top
                self.delete_button.show()

    def clear(self):
        self.setText(self.tr("Drop folder here or click to select"))
        self.folderPath = ""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.delete_button.hide()
