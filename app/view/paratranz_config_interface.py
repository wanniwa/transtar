from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QTextEdit
from PySide6.QtGui import QDesktopServices
from qfluentwidgets import (TitleLabel, SubtitleLabel, LineEdit,
                            PrimaryPushButton, SimpleCardWidget, FluentIcon as FIF,
                            InfoBar, TextBrowser)
from ..common.config import cfg


class ParatranzConfigInterface(QWidget):
    """ParaTranz配置界面"""

    configCompleted = Signal()  # 配置完成信号
    configChanged = Signal()  # 添加配置变更信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ParatranzConfigInterface")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # 标题
        titleLabel = TitleLabel(self.tr('ParaTranz Configuration'), self)
        layout.addWidget(titleLabel)

        # 说明文本 - 使用QTextBrowser替代QTextEdit
        self.guideText = TextBrowser(self)


        # 先设置允许打开外部链接
        self.guideText.setOpenExternalLinks(True)

        # 使用HTML格式的文本，添加链接
        guide_html = self.tr('''Follow these steps to start using the dictionary feature:<br>

1. Register an account at <a href="https://paratranz.cn">paratranz.cn</a> <br>
2. Create a new project at <a href="https://paratranz.cn/projects/create">paratranz.cn/projects/create</a> <br>
3. Get your token from <a href="https://paratranz.cn/settings">https://paratranz.cn/users/my</a> (Click your avatar at top-right -> Settings)<br>
4. Get project ID from your project URL (e.g., for paratranz.cn/projects/3135, ID is 3135)<br>
5. Configure your token and project ID below''')

        # 然后设置HTML内容
        self.guideText.setText(guide_html)

        # 调整高度以适应内容
        self.guideText.setFixedHeight(150)
        layout.addWidget(self.guideText)

        # Token输入框
        tokenCard = SimpleCardWidget()
        tokenLayout = QVBoxLayout(tokenCard)
        tokenLayout.setContentsMargins(20, 20, 20, 20)
        tokenLayout.setSpacing(10)

        tokenLabel = SubtitleLabel(self.tr('ParaTranz Token'), self)
        tokenTip = QTextEdit(self)
        tokenTip.setReadOnly(True)
        tokenTip.setFrameStyle(0)
        tokenTip.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: #666666;
                font-size: 14px;
            }
        """)
        tokenTip.setText(self.tr('Found in your ParaTranz profile settings'))
        tokenTip.setFixedHeight(25)
        self.tokenEdit = LineEdit(self)
        self.tokenEdit.setPlaceholderText(self.tr('Enter your ParaTranz token'))
        self.tokenEdit.setText(cfg.paratranz_token.value)

        tokenLayout.addWidget(tokenLabel)
        tokenLayout.addWidget(tokenTip)
        tokenLayout.addWidget(self.tokenEdit)
        layout.addWidget(tokenCard)

        # Project ID输入框
        projectCard = SimpleCardWidget()
        projectLayout = QVBoxLayout(projectCard)
        projectLayout.setContentsMargins(20, 20, 20, 20)
        projectLayout.setSpacing(10)

        projectLabel = SubtitleLabel(self.tr('Project ID'), self)
        projectTip = QTextEdit(self)
        projectTip.setReadOnly(True)
        projectTip.setFrameStyle(0)
        projectTip.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                color: #666666;
                font-size: 14px;
            }
        """)
        projectTip.setText(self.tr('The number in your project URL'))
        projectTip.setFixedHeight(25)
        self.projectEdit = LineEdit(self)
        self.projectEdit.setPlaceholderText(self.tr('Enter your project ID'))
        self.projectEdit.setText(cfg.paratranz_project_id.value)

        projectLayout.addWidget(projectLabel)
        projectLayout.addWidget(projectTip)
        projectLayout.addWidget(self.projectEdit)
        layout.addWidget(projectCard)

        # 按钮布局
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(20)

        # ParaTranz按钮
        self.paratranzBtn = PrimaryPushButton(self.tr('Go to ParaTranz'), self, icon=FIF.LINK)
        self.paratranzBtn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://paratranz.cn')))

        # 确认按钮
        self.confirmButton = PrimaryPushButton(self.tr('Confirm'), self)
        self.confirmButton.clicked.connect(self.save_config)

        buttonLayout.addWidget(self.paratranzBtn)
        buttonLayout.addWidget(self.confirmButton)

        layout.addLayout(buttonLayout)
        layout.addStretch()

    def save_config(self):
        """保存配置"""
        token = self.tokenEdit.text().strip()
        project_id = self.projectEdit.text().strip()

        if not token or not project_id:
            InfoBar.warning(
                self.tr('Warning'),
                self.tr('Please enter both token and project ID'),
                parent=self
            )
            return

        # 保存配置
        cfg.set(cfg.paratranz_token, token)
        cfg.set(cfg.paratranz_project_id, project_id)

        # 发送配置完成信号
        self.configCompleted.emit()
