from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from qfluentwidgets import MessageBoxBase, SubtitleLabel, BodyLabel, PlainTextEdit, PushButton

from app.common.utils.file_util import open_folder


class FileErrorDialog(MessageBoxBase):
    """文件错误对话框 - 使用 qfluentwidgets 风格"""
    
    def __init__(self, e, tb, parent=None):
        super().__init__(parent)
        self.tb = tb
        
        # 设置对话框大小
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(400)
        
        # 保存完整的错误信息以供复制
        self.full_error_text = f"{e.__class__.__name__}\n{tb}\n\n{str(e)}"
        
        # 配置默认按钮
        self.yesButton.setText(self.tr('OK'))
        self.cancelButton.hide()
        
        # 设置主布局边距
        self.viewLayout.setContentsMargins(24, 24, 24, 24)
        self.viewLayout.setSpacing(16)
        
        # 错误类型标题
        self.titleLabel = SubtitleLabel(e.__class__.__name__, self)
        self.titleLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.viewLayout.addWidget(self.titleLabel)
        
        # 文件路径
        self.pathLabel = BodyLabel(tb, self)
        self.pathLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.pathLabel.setWordWrap(True)
        self.viewLayout.addWidget(self.pathLabel)
        
        # 详细错误信息文本框
        self.detailsEdit = PlainTextEdit(self)
        self.detailsEdit.setPlainText(str(e))
        self.detailsEdit.setReadOnly(True)
        self.detailsEdit.setMinimumHeight(200)
        self.viewLayout.addWidget(self.detailsEdit)
        
        # 添加自定义按钮到按钮布局
        self.copyButton = PushButton(self.tr('Copy Error'), self)
        self.copyButton.clicked.connect(self._copy_error)
        self.buttonLayout.insertWidget(0, self.copyButton)
        
        self.openFileButton = PushButton(self.tr('Open File'), self)
        self.openFileButton.clicked.connect(lambda: open_folder(tb))
        self.buttonLayout.insertWidget(1, self.openFileButton)
        
        # 添加弹性空间使按钮靠右
        self.buttonLayout.insertStretch(0)
    
    def _copy_error(self):
        """复制完整的错误信息到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.full_error_text)
