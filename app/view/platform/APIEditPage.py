from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QVBoxLayout

from qfluentwidgets import PlainTextEdit
from qfluentwidgets import MessageBoxBase
from qfluentwidgets import SingleDirectionScrollArea

from app.core.TransBase import TransBase
from app.view.components.GroupCard import GroupCard
from app.view.components.ComboBoxCard import ComboBoxCard
from app.view.components.LineEditCard import LineEditCard
from app.view.components.SwitchButtonCard import SwitchButtonCard
from app.view.components.EditableComboBoxCard import EditableComboBoxCard


class APIEditPage(MessageBoxBase, TransBase):

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

        # # 设置滚动器
        # self.scroller = SingleDirectionScrollArea(self, orient=Qt.Orientation.Vertical)
        # self.scroller.setWidgetResizable(True)
        # self.scroller.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        # self.viewLayout.addWidget(self.scroller)

        # 设置滚动控件
        self.vbox_parent = QWidget(self)
        self.vbox_parent.setStyleSheet("QWidget { background: transparent; }")
        self.vbox = QVBoxLayout(self.vbox_parent)
        self.vbox.setSpacing(8)
        self.vbox.setContentsMargins(24, 24, 24, 24)  # 左、上、右、下
        # self.scroller.setWidget(self.vbox_parent)
        self.viewLayout.addWidget(self.vbox_parent)



        # 接口地址
        if "api_url" in config.get("platforms").get(self.key).get("key_in_settings"):
            self.add_widget_url(self.vbox, config)

        # 接口地址自动补全
        if "auto_complete" in config.get("platforms").get(self.key).get("key_in_settings"):
            self.add_widget_auto_complete(self.vbox, config)

        # 接口密钥
        if "api_key" in config.get("platforms").get(self.key).get("key_in_settings"):
            self.add_widget_key(self.vbox, config)

        # 接口区域
        if "region" in config.get("platforms").get(self.key).get("key_in_settings"):
            self.add_widget_region(self.vbox, config)

        # 接口密钥
        if "access_key" in config.get("platforms").get(self.key).get("key_in_settings"):
            self.add_widget_access_key(self.vbox, config)

        # 接口密钥
        if "secret_key" in config.get("platforms").get(self.key).get("key_in_settings"):
            self.add_widget_secret_key(self.vbox, config)

        # 接口格式
        if "api_format" in config.get("platforms").get(self.key).get("key_in_settings"):
            self.add_widget_format(self.vbox, config)

        # 模型名称
        if "model" in config.get("platforms").get(self.key).get("key_in_settings"):
            self.add_widget_model(self.vbox, config)

        # 填充
        self.vbox.addStretch(1)

    # 接口地址
    def add_widget_url(self, parent, config):
        def init(widget):
            widget.set_text(config.get("platforms").get(self.key).get("api_url"))
            widget.set_fixed_width(256)
            info_cont = self.tr("Please enter interface URL") + " ..."
            widget.set_placeholder_text(info_cont)

        def text_changed(widget, text: str):
            config = self.load_config()
            config["platforms"][self.key]["api_url"] = text.strip()
            self.save_config(config)

        parent.addWidget(
            LineEditCard(
                self.tr("Interface URL"),
                self.tr("Please enter interface URL, for example https://api.deepseek.com"),
                init=init,
                text_changed=text_changed,
            )
        )

    # 接口地址自动补全
    def add_widget_auto_complete(self, parent, config):
        def init(widget):
            widget.set_checked(config.get("platforms").get(self.key).get("auto_complete"))

        def checked_changed(widget, checked: bool):
            config = self.load_config()
            config["platforms"][self.key]["auto_complete"] = checked
            self.save_config(config)

        parent.addWidget(
            SwitchButtonCard(
                self.tr("Interface URL auto-completion"),
                self.tr("Will automatically fill in the interface URL for you, for example https://api.deepseek.com -> https://api.deepseek.com/v1"),
                init=init,
                checked_changed=checked_changed,
            )
        )

    # 接口密钥
    def add_widget_key(self, parent, config):

        def text_changed(widget):
            config = self.load_config()
            config["platforms"][self.key]["api_key"] = widget.toPlainText().strip()
            self.save_config(config)

        def init(widget):
            plain_text_edit = PlainTextEdit(self)
            plain_text_edit.setPlainText(config.get("platforms").get(self.key).get("api_key"))
            plain_text_edit.setPlaceholderText(self.tr("Please enter interface key"))
            plain_text_edit.textChanged.connect(lambda: text_changed(plain_text_edit))
            widget.addWidget(plain_text_edit)

        parent.addWidget(
            GroupCard(
                self.tr("Interface key"),
                self.tr("Please enter interface key, for example sk-d0daba12345678fd8eb7b8d31c123456, separate multiple keys with comma (,)"),
                init=init,
            )
        )

    # 接口密钥
    def add_widget_access_key(self, parent, config):

        def text_changed(widget):
            config = self.load_config()
            config["platforms"][self.key]["access_key"] = widget.toPlainText().strip()
            self.save_config(config)

        def init(widget):
            plain_text_edit = PlainTextEdit(self)
            plain_text_edit.setPlainText(config.get("platforms").get(self.key).get("access_key"))
            plain_text_edit.setPlaceholderText(self.tr("Please enter AWS Access Key"))
            plain_text_edit.textChanged.connect(lambda: text_changed(plain_text_edit))
            widget.addWidget(plain_text_edit)

        parent.addWidget(
            GroupCard(
                self.tr("AWS Access Key"),
                self.tr("Please enter AWS Access Key"),
                init=init,
            )
        )

    # 接口密钥
    def add_widget_secret_key(self, parent, config):

        def text_changed(widget):
            config = self.load_config()
            config["platforms"][self.key]["secret_key"] = widget.toPlainText().strip()
            self.save_config(config)

        def init(widget):
            plain_text_edit = PlainTextEdit(self)
            plain_text_edit.setPlainText(config.get("platforms").get(self.key).get("secret_key"))
            plain_text_edit.setPlaceholderText(self.tr("Please enter AWS Secret Key"))
            plain_text_edit.textChanged.connect(lambda: text_changed(plain_text_edit))
            widget.addWidget(plain_text_edit)

        parent.addWidget(
            GroupCard(
                self.tr("AWS Secret Key"),
                self.tr("Please enter AWS Secret Key"),
                init=init,
            )
        )

    # 接口区域
    def add_widget_region(self, parent, config):

        def init(widget):
            platforms = config.get("platforms").get(self.key)

            # 如果默认区域列表中不存在该条目，则添加
            items = platforms.get("region_datas")
            if platforms.get("region") != "" and platforms.get("region") not in platforms.get("region_datas"):
                items.append(platforms.get("region"))

            widget.set_items(items)
            widget.set_fixed_width(256)
            widget.set_current_index(max(0, widget.find_text(platforms.get("region"))))
            widget.set_placeholder_text(self.tr("Please enter region"))

        def current_text_changed(widget, text: str):
            config = self.load_config()
            config["platforms"][self.key]["region"] = text.strip()
            self.save_config(config)

        def items_changed(widget, items: list[str]):  # 处理 items_changed 信号的槽函数
            config = self.load_config()
            config["platforms"][self.key]["region_datas"] = items  # 更新 region_datas
            self.save_config(config)  # 保存配置

        card = EditableComboBoxCard(
                            self.tr("Region (editable)"),
                self.tr("Please select or enter the region to use"),
            [],
            init=init,
            current_text_changed=current_text_changed,
        )
        card.items_changed.connect(lambda items: items_changed(card, items))  # 连接信号
        parent.addWidget(card)

    # 接口格式
    def add_widget_format(self, parent, config):
        def init(widget):
            platform = config.get("platforms").get(self.key)

            widget.set_items(platform.get("format_datas"))
            widget.set_current_index(max(0, widget.find_text(platform.get("api_format"))))

        def current_text_changed(widget, text: str):
            config = self.load_config()
            config["platforms"][self.key]["api_format"] = text.strip()
            self.save_config(config)

        parent.addWidget(
            ComboBoxCard(
                self.tr("Interface format"),
                self.tr("Please select interface format, most models use OpenAI format, some relay station Claude models use Anthropic format"),
                [],
                init=init,
                current_text_changed=current_text_changed,
            )
        )

    # 模型名称
    def add_widget_model(self, parent, config):
        def init(widget):
            platforms = config.get("platforms").get(self.key)

            # 如果默认模型列表中不存在该条目，则添加
            items = platforms.get("model_datas")
            if platforms.get("model") != "" and platforms.get("model") not in platforms.get("model_datas"):
                items.append(platforms.get("model"))

            widget.set_items(items)
            widget.set_fixed_width(256)
            widget.set_current_index(max(0, widget.find_text(platforms.get("model"))))
            widget.set_placeholder_text(self.tr("Please enter model name"))

        def current_text_changed(widget, text: str):
            config = self.load_config()
            config["platforms"][self.key]["model"] = text.strip()
            self.save_config(config)

        def items_changed(widget, items: list[str]):  # 处理 items_changed 信号的槽函数
            config = self.load_config()
            config["platforms"][self.key]["model_datas"] = items  # 更新 model_datas
            self.save_config(config)  # 保存配置

        card = EditableComboBoxCard(
                            self.tr("Model name (editable)"),
                self.tr("Please select or enter the name of the model to use"),
            [],
            init=init,
            current_text_changed=current_text_changed,
        )
        card.items_changed.connect(lambda items: items_changed(card, items))  # 连接信号
        parent.addWidget(card)
