from PySide6.QtWidgets import QDialog, QLabel, QTextEdit, QVBoxLayout
from qfluentwidgets import PushButton

from app.common.utils.file_util import open_folder

class FileErrorDialog(QDialog):
    def __init__(self, e, tb, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error")
        self.resize(600, 400)
        self.label = QLabel(e.__class__.__name__, self)
        self.info = QLabel(str(e), self)
        self.details = QTextEdit(tb, self)
        self.details.setReadOnly(True)

        self.open_file_button = PushButton()
        self.open_file_button.setText(self.tr('Open File'))
        self.open_file_button.clicked.connect(lambda: open_folder(tb))

        self.button = PushButton()
        self.button.setText(self.tr('OK'))
        self.button.clicked.connect(self.close)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.info)
        self.layout.addWidget(self.details)
        self.layout.addWidget(self.open_file_button)  # 将新按钮添加到布局中
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
