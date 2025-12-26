from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout

from qfluentwidgets import MessageBoxBase
from qfluentwidgets import SingleDirectionScrollArea

from app.core.TransBase import TransBase
from app.view.components.SpinCard import SpinCard


class LimitEditPage(MessageBoxBase, TransBase):

    def __init__(self, window, key):
        super().__init__(window)

        # 初始化
        self.key = key

        # 设置框体
        # self.widget.setFixedSize(960, 720)
        self.yesButton.setText(self.tr("Close"))
        self.cancelButton.hide()

        # 载入配置文件
        config = self.load_config()

        # 设置主布局
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        # 设置滚动控件
        self.vbox_parent = QWidget(self)
        self.vbox_parent.setStyleSheet("QWidget { background: transparent; }")
        self.vbox = QVBoxLayout(self.vbox_parent)
        self.vbox.setSpacing(8)
        self.vbox.setContentsMargins(24, 24, 24, 24)  # 左、上、右、下
        self.viewLayout.addWidget(self.vbox_parent)

        # 添加控件
        self.add_widget_rpm(self.vbox, config)
        self.add_widget_tpm(self.vbox, config)

        # 填充
        self.vbox.addStretch(1)

    # 每分钟请求数
    def add_widget_rpm(self, parent, config):
        def init(widget):
            widget.set_range(0, 9999999)
            widget.set_value(config.get("platforms").get(self.key).get("rpm_limit", 4096))

        def value_changed(widget, value: str):
            config = self.load_config()
            config["platforms"][self.key]["rpm_limit"] = value
            self.save_config(config)

        parent.addWidget(
            SpinCard(
                self.tr("Requests per minute"),
                self.tr("RPM, the maximum number of requests each key can respond to in one minute"),
                init=init,
                value_changed=value_changed,
            )
        )

    # 每分钟 Token 数
    def add_widget_tpm(self, parent, config):
        def init(widget):
            widget.set_range(0, 9999999)
            widget.set_value(config.get("platforms").get(self.key).get("tpm_limit", 4096000))

        def value_changed(widget, value: str):
            config = self.load_config()
            config["platforms"][self.key]["tpm_limit"] = value
            self.save_config(config)

        parent.addWidget(
            SpinCard(
                self.tr("Tokens per minute"),
                self.tr("TPM, the maximum number of tokens each key can generate in one minute"),
                init=init,
                value_changed=value_changed,
            )
        )
