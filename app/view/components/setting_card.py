from typing import Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QVBoxLayout, QTextEdit
from qfluentwidgets import LineEdit, SettingCard, FluentIconBase, ConfigItem, TextEdit, ExpandSettingCard
from app.common.config import cfg


class LineEditSettingCard(SettingCard):
    """ Setting card with a push button """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None,
                 configItem: ConfigItem = None, parent=None):
        """
        Parameters
        ----------
        text: str
            the text of push button

        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.lineEdit = LineEdit(self)
        self.lineEdit.setMinimumWidth(200)
        self.lineEdit.setText(configItem.value)
        self.hBoxLayout.addWidget(self.lineEdit, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.lineEdit.textChanged.connect(self.setValue)

    def setValue(self, value):
        cfg.set(self.configItem, value)


class TextEditSettingCard(ExpandSettingCard):
    """ Setting card with a large text edit in vertical layout """

    def __init__(self, icon: Union[str, QIcon, FluentIconBase], title, content=None, placeholder=None,
                 configItem: ConfigItem = None, parent=None):
        """
        Parameters
        ----------
        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        placeholder: str
            placeholder text shown when text edit is empty

        configItem: ConfigItem
            the config item to store value

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)
        self.configItem = configItem

        # 创建文本编辑框
        self.textEdit = QTextEdit(self.view)
        self.textEdit.setText(configItem.value)
        self.textEdit.setFixedHeight(100)
        
        # 设置占位符文本
        if placeholder:
            self.textEdit.setPlaceholderText(placeholder)

        # 使用 ExpandSettingCard 提供的 viewLayout
        self.viewLayout.setContentsMargins(10, 0, 10, 0)
        self.viewLayout.addWidget(self.textEdit)

        self._adjustViewSize()

        # 连接信号
        self.textEdit.textChanged.connect(self._handleTextChanged)

    def _handleTextChanged(self):
        """ 处理文本变化 """
        cfg.set(self.configItem, self.textEdit.toPlainText())
