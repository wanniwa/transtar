import os
import json
import copy
import random
from functools import partial

from PySide6.QtCore import QUrl, Signal, Qt, QMimeData
from PySide6.QtGui import QDesktopServices, QIcon, QDrag
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel

from qfluentwidgets import Action, CaptionLabel, DropDownPushButton, HorizontalSeparator, PrimaryPushButton, InfoBar, \
    InfoBarPosition, StrongBodyLabel
from qfluentwidgets import RoundMenu
from qfluentwidgets import FluentIcon
from qfluentwidgets import PushButton

from app.core.TransBase import TransBase
from app.common.config import appConfig
from app.view.components.APITypeCard import APITypeCard
from app.view.components.LineEditMessageBox import LineEditMessageBox
from app.view.platform.APIEditPage import APIEditPage
from app.view.platform.ArgsEditPage import ArgsEditPage
from app.view.platform.LimitEditPage import LimitEditPage


# 可拖动的接口按钮类,继承 DropDownPushButton，添加拖放功能
class DraggableAPIButton(DropDownPushButton):
    def __init__(self, *args, api_tag: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self.api_tag = api_tag  # 存储接口的唯一标识


class PlatformInterface(QFrame, TransBase):
    # 自定义平台默认配置
    CUSTOM = {
        "tag": "",
        "group": "custom",
        "name": "",
        "api_url": "https://api.lingyiwanwu.com/v1",
        "api_key": "",
        "api_format": "OpenAI",
        "rpm_limit": 4096,
        "tpm_limit": 8000000,
        "model": "gpt-4o",
        "top_p": 1.0,
        "temperature": 1.0,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "think_switch": False,
        "think_depth": "low",
        "auto_complete": True,

        "model_datas": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "claude-3-5-haiku",
            "claude-3-5-sonnet",
        ],
        "format_datas": [
            "ChatGPT",
            "Claude",
            "Gemini"
        ],
        "extra_body": {},
        "key_in_settings": [
            "api_url",
            "api_key",
            "api_format",
            "rpm_limit",
            "tpm_limit",
            "model",
            "auto_complete",
            "top_p",
            "temperature",
            "presence_penalty",
            "frequency_penalty",
            "extra_body",
            "think_switch",
            "think_depth",
            "thinking_budget"
        ],
    }

    def __init__(self, window):
        super().__init__(window)
        self.setObjectName("platform_interface")

        self.window = window  # 全局变量
        self.load_preset()  # 读取合并配置

        self.container = QVBoxLayout(self)
        self.container.setSpacing(15)  # 增加间距以容纳新卡片
        self.container.setContentsMargins(24, 24, 24, 24)

        # 读取合并配置
        config = self.save_config(self.load_config_from_default())

        # 顶部：当前翻译提供方展示
        self.add_current_translation_widget(self.container, config)

        # 布局组件
        self.add_api_widget(self.container, config)
        self.add_official_widget(self.container, config)
        self.add_custom_widget(self.container, config)

        # 添加分割线
        self.container.addWidget(HorizontalSeparator())

        self.container.addStretch(1)
        self.subscribe(TransBase.EVENT.API_TEST_DONE, self.api_test_done)

    # 顶部展示：当前翻译提供方
    def add_current_translation_widget(self, parent, config):
        wrapper = QFrame(self)
        wrapper.setObjectName("current_provider_card")
        # 更明显的外观：描边、圆角、浅底色
        wrapper.setStyleSheet(
            """
            QFrame#current_provider_card {
                border: 1px solid rgba(120, 120, 120, 0.30);
                border-radius: 8px;
                background-color: rgba(127, 127, 127, 0.05);
            }
            """
        )
        h = QHBoxLayout(wrapper)
        h.setContentsMargins(16, 12, 16, 12)
        h.setSpacing(12)

        title_label = StrongBodyLabel(self.tr("Current translation provider: "), self)
        self.current_provider_icon = QLabel(self)
        self.current_provider_icon.setFixedSize(24, 24)
        self.current_provider_value = CaptionLabel("", self)
        self.current_provider_model = CaptionLabel("", self)

        h.addWidget(title_label)
        h.addWidget(self.current_provider_icon)
        h.addWidget(self.current_provider_value)
        h.addWidget(self.current_provider_model)
        h.addStretch(1)

        parent.addWidget(wrapper)
        self.update_current_translation_display(config)

    def update_current_translation_display(self, config=None):
        if config is None:
            config = self.load_config()

        name, icon, model = self.get_current_translation_info(config)
        self.current_provider_value.setText(name)
        # 模型（仅 AI 展示）
        if model:
            self.current_provider_model.setText(f"({model})")
            self.current_provider_model.show()
        else:
            self.current_provider_model.clear()
            self.current_provider_model.hide()

        # 设置图标
        if icon:
            icon_name = icon
            icon_path = os.path.join("app", "resource", "images", "platforms", icon_name)
            if os.path.exists(icon_path):
                self.current_provider_icon.setPixmap(QIcon(icon_path).pixmap(24, 24))
            else:
                self.current_provider_icon.clear()
        else:
            self.current_provider_icon.clear()

    def get_current_translation_info(self, config) -> tuple[str, str | None, str | None]:
        # 优先根据保存的 trans_platform（平台 tag）确定
        trans_tag = config.get("trans_platform")
        platforms = config.get("platforms", {})
        if trans_tag and trans_tag in platforms:
            v = platforms[trans_tag]
            return v.get("name", trans_tag), v.get("icon"), v.get("model")
        # 回退默认 Google
        return "Google", "google", None

    # 从文件加载
    def load_file(self, path: str) -> dict:
        result = {}

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as reader:
                result = json.load(reader)
        else:
            self.error(self.tr("Can't find the file:") + path)

        return result

    # 执行接口测试
    def api_test(self, tag: str, *args):
        # 载入配置文件
        config = self.load_config()
        platform = config.get("platforms").get(tag)
        if TransBase.work_status == TransBase.STATUS.IDLE:
            # 更新运行状态
            TransBase.work_status = TransBase.STATUS.API_TEST

            # 创建事件参数
            data = copy.deepcopy(platform)

            # 触发事件
            self.event_emit(TransBase.EVENT.API_TEST_START, data)
        else:
            self.warning_toast("", self.tr("API test is running, please try again later"))

    # 接口测试完成
    def api_test_done(self, event: int, data: dict):
        # 更新运行状态
        TransBase.work_status = TransBase.STATUS.IDLE

        if len(data.get("failure", [])) > 0:
            info_cont = self.tr(
                "API test results: Success") + f"   {len(data.get('success', []))}" + "......" + self.tr(
                "Failed") + f"   {len(data.get('failure', []))}" + "......"
            self.error_toast("", info_cont)
        else:
            info_cont = self.tr("API test results: Success") + f"   {len(data.get('success', []))}"
            self.success_toast("", info_cont)

    # 设为翻译提供方
    def set_as_translation_provider(self, tag: str, *args) -> None:
        config = self.load_config()
        # 使用 TransBase 配置保存所选平台 TAG，供全局翻译使用
        config["trans_platform"] = tag
        self.save_config(config)

        # 更新顶部展示
        self.update_current_translation_display(config)

    # 加载并更新预设配置
    def load_preset(self):
        # 这个函数的主要目的是保证可以通过预设文件对内置的接口的固定属性进行更新
        preset = self.load_file("app/resource/default/preset.json")
        config = self.load_config()

        # 从配置文件中非自定义读取接口信息数据并使用预设数据更新
        p_platforms = preset.get("platforms", {})
        c_platforms = config.get("platforms", {})
        # 遍历预设数据中的接口信息
        for k, p_platform in p_platforms.items():
            # 在配置数据中查找相同的接口
            if k in c_platforms:
                c_platform = c_platforms.get(k, {})
                # 如果该字段属于用户自定义字段，且配置数据中该字段的值合法，则使用此值更新预设数据
                for setting in p_platform.get("key_in_settings", []):
                    if c_platform.get(setting, None) != None:
                        p_platform[setting] = c_platform.get(setting, None)

        # 从配置文件中读取自定义接口信息数据并使用预设数据更新
        custom = {k: v for k, v in config.get("platforms", {}).items() if v.get("group") == "custom"}
        # 遍历自定义模型数据
        for _, platform in custom.items():
            for k, v in self.CUSTOM.items():
                # 如果该字段的值不合法，则使用预设数据更新该字段的值
                if platform.get(k, None) == None:
                    platform[k] = v

                # 如果字段不属于用户自定义字段，且不在保护字段范围内，则使用预设数据更新该字段的值！！！
                if k not in self.CUSTOM.get("key_in_settings", []) and k not in ("tag", "name", "group", "model_datas",
                                                                                 "extra_body"):
                    platform[k] = v

        # 汇总数据并更新配置数据中的接口信息
        platforms = {}
        platforms.update(preset.get("platforms", {}))
        platforms.update(custom)
        config["platforms"] = platforms

        # 保存并返回
        return self.save_config(config)

    # 删除平台
    def delete_platform(self, tag: str, *args) -> None:
        # 载入配置文件
        config = self.load_config()

        # 删除对应的平台
        del config["platforms"][tag]

        # 保存配置文件
        self.save_config(config)

        # 更新所有控件
        self.update_custom_platform_widgets(self.flow_card)

    # 重命名平台
    def rename_platform(self, tag: str, *args) -> None:
        # 定义对话框关闭时的回调函数
        def message_box_close(widget, new_name: str):
            if not new_name.strip():
                self.warning_toast("", self.tr("Interface name cannot be empty"))
                return

            config = self.load_config()

            # 检查平台是否存在
            if tag not in config["platforms"]:
                self.error_toast("", self.tr("Interface does not exist"))
                return

            # 更新平台名称
            config["platforms"][tag]["name"] = new_name.strip()

            # 保存配置文件
            self.save_config(config)

            # 更新所有控件
            self.update_custom_platform_widgets(self.flow_card)

            self.success_toast("", self.tr("Interface renamed successfully"))

        # 载入配置文件
        config = self.load_config()

        # 检查平台是否存在
        if tag not in config["platforms"]:
            self.error_toast("", self.tr("Interface does not exist"))
            return

        current_name = config["platforms"][tag].get("name", "")

        message_box = LineEditMessageBox(
            self.window,
            self.tr("Please enter new interface name"),
            message_box_close=message_box_close,
            default_text=current_name  # 设置默认文本为当前名称
        )

        message_box.exec()

    # 生成 UI 描述数据
    def generate_ui_datas(self, platforms: dict, is_custom: bool) -> list:
        ui_datas = []

        for k, v in platforms.items():
            # k 就是 tag，我们需要把它传递下去
            base_data = {
                "tag": k,
                "name": v.get("name"),
                "icon": v.get("icon"),
            }

            if not is_custom:
                if v.get("api_format") == "google":
                    # 翻译接口：仅提供选择为翻译与测试
                    base_data["menus"] = [
                        (FluentIcon.ACCEPT, self.tr("Use For Translation"), partial(self.set_as_translation_provider, k)),
                        (FluentIcon.SEND, self.tr("Test Interface"), partial(self.api_test, k)),
                    ]
                elif v.get("api_format") == "deepl":
                    base_data["menus"] = [
                        (FluentIcon.ACCEPT, self.tr("Use For Translation"), partial(self.set_as_translation_provider, k)),
                        (FluentIcon.EDIT, self.tr("Edit Interface"), partial(self.show_api_edit_page, k)),
                        (FluentIcon.SEND, self.tr("Test Interface"), partial(self.api_test, k)),
                    ]
                else:
                    # AI 接口：完整菜单并提供选择为翻译
                    base_data["menus"] = [
                        (FluentIcon.ACCEPT, self.tr("Use For Translation"), partial(self.set_as_translation_provider, k)),
                        (FluentIcon.EDIT, self.tr("Edit Interface"), partial(self.show_api_edit_page, k)),
                        (FluentIcon.SCROLL, self.tr("Edit Rate Limit"), partial(self.show_limit_edit_page, k)),
                        (FluentIcon.DEVELOPER_TOOLS, self.tr("Edit Parameters"), partial(self.show_args_edit_page, k)),
                        (FluentIcon.SEND, self.tr("Test Interface"), partial(self.api_test, k)),
                    ]
            else:
                base_data["menus"] = [
                    (FluentIcon.ACCEPT, self.tr("Use For Translation"), partial(self.set_as_translation_provider, k)),
                    (FluentIcon.EDIT, self.tr("Edit Interface"), partial(self.show_api_edit_page, k)),
                    (FluentIcon.LABEL, self.tr("Rename Interface"), partial(self.rename_platform, k)),
                    (FluentIcon.SCROLL, self.tr("Edit Rate Limit"), partial(self.show_limit_edit_page, k)),
                    (FluentIcon.DEVELOPER_TOOLS, self.tr("Edit Parameters"), partial(self.show_args_edit_page, k)),
                    (FluentIcon.DELETE, self.tr("Delete Interface"), partial(self.delete_platform, k)),
                    (FluentIcon.SEND, self.tr("Test Interface"), partial(self.api_test, k)),
                ]
            ui_datas.append(base_data)
        return ui_datas

    # 显示编辑接口对话框
    def show_api_edit_page(self, key: str, *args):
        APIEditPage(self.window, key).exec()

    # 显示编辑参数对话框
    def show_args_edit_page(self, key: str, *args):
        ArgsEditPage(self.window, key).exec()

    # 显示编辑限额对话框
    def show_limit_edit_page(self, key: str, *args):
        LimitEditPage(self.window, key).exec()

    # 初始化按钮的方法
    def init_drop_down_push_button(self, widget, datas):
        for item in datas:
            # 使用新的可拖动按钮类
            drop_down_push_button = DraggableAPIButton(
                item.get("name"),
                api_tag=item.get("tag")  # 传递 api_tag
            )

            if item.get("icon"):
                icon_name = item.get("icon")
                icon_path = os.path.join("app", "resource", "images", "platforms", icon_name)
                drop_down_push_button.setIcon(QIcon(icon_path))

            drop_down_push_button.setFixedWidth(192)
            drop_down_push_button.setContentsMargins(4, 0, 4, 0)

            widget.add_widget(drop_down_push_button)

            menu = RoundMenu(item.get("name"))
            for k, v in enumerate(item.get("menus")):
                menu.addAction(Action(v[0], v[1], triggered=v[2]))
                if k != len(item.get("menus")) - 1:
                    menu.addSeparator()
            drop_down_push_button.setMenu(menu)

    # 初始化简单按钮（无下拉菜单）
    def init_simple_buttons(self, widget, datas):
        for item in datas:
            button = PushButton(item.get("name"))
            # 设置图标（如果有）
            if item.get("icon"):
                icon_name = item.get("icon") + '.png'
                icon_path = os.path.join("app", "resource", "images", "platforms", icon_name)
                button.setIcon(QIcon(icon_path))

            button.setFixedWidth(192)
            button.setContentsMargins(4, 0, 4, 0)
            widget.add_widget(button)

            # 点击直接进入接口编辑页
            tag = item.get("tag")
            button.clicked.connect(partial(self.show_api_edit_page, tag))

    # 更新自定义平台控件
    def update_custom_platform_widgets(self, widget):
        config = self.load_config()
        platforms = {k: v for k, v in config.get("platforms").items() if v.get("group") == "custom"}

        widget.take_all_widgets()
        self.init_drop_down_push_button(
            widget,
            self.generate_ui_datas(platforms, True)
        )

    # 添加头部-接口（仅展示 Google 类型，无下拉配置）
    def add_api_widget(self, parent, config):
        def init(widget):
            # 更新子控件：展示翻译接口，使用下拉菜单
            self.init_drop_down_push_button(
                widget,
                self.generate_ui_datas(platforms, False),
            )

        # 接口数据：筛选为翻译接口（group == "api"）
        platforms = {k: v for k, v in config.get("platforms").items() if v.get("group") == "api"}
        parent.addWidget(
            APITypeCard(
                self.tr("Interface"),
                self.tr("Manage translation interfaces"),
                icon=FluentIcon.CONNECT,
                init=init,
            )
        )

    # 添加主体-AI（原"官方接口"）
    def add_official_widget(self, parent, config):

        # 展示所有在线AI接口
        platforms = {k: v for k, v in config.get("platforms").items() if v.get("group") == "ai"}
        parent.addWidget(
            APITypeCard(
                self.tr("AI"),
                self.tr("Manage built-in mainstream AI interfaces"),
                icon=FluentIcon.ROBOT,
                init=lambda widget: self.init_drop_down_push_button(
                    widget,
                    self.generate_ui_datas(platforms, False),
                ),
            )
        )

    # 添加底部-自定义接口
    def add_custom_widget(self, parent, config):

        def message_box_close(widget, text: str):
            config = self.load_config()

            # 生成一个随机 TAG
            tag = f"custom_platform_{random.randint(100000, 999999)}"

            # 修改和保存配置
            platform = copy.deepcopy(self.CUSTOM)
            platform["tag"] = tag
            platform["name"] = text.strip()
            config["platforms"][tag] = platform
            self.save_config(config)

            # 更新ui
            self.update_custom_platform_widgets(self.flow_card)

        def on_add_button_clicked(widget):
            message_box = LineEditMessageBox(
                self.window,
                self.tr("Please enter new AI interface name"),
                message_box_close=message_box_close
            )

            message_box.exec()

        def init(widget):
            # 添加新增按钮
            add_button = PrimaryPushButton(self.tr("Add"))
            add_button.setIcon(FluentIcon.ADD_TO)
            add_button.setContentsMargins(4, 0, 4, 0)
            add_button.clicked.connect(lambda: on_add_button_clicked(self))
            widget.add_widget_to_head(add_button)

            # 更新ui
            self.update_custom_platform_widgets(widget)

        self.flow_card = APITypeCard(
            self.tr("Custom AI"),
            self.tr("Add and manage any large language model interfaces that comply with OpenAI or Anthropic formats"),
            icon=FluentIcon.ASTERISK,
            init=init,
        )
        parent.addWidget(self.flow_card)
