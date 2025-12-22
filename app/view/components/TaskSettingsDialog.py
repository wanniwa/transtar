# coding:utf-8
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (MessageBoxBase, SubtitleLabel, SettingCardGroup,
                            SettingCard, ComboBox, SpinBox, FluentIcon, InfoBar, ScrollArea, qconfig, 
                            ExpandSettingCard, PlainTextEdit)

from app.common.config import appConfig, load_config
from app.common.setting import TRANS_CONFIG_FILE


class TaskSettingsDialog(MessageBoxBase):
    """任务设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 载入平台配置（platforms信息仍从trans_config.json读取）
        self.platforms_config = load_config(str(TRANS_CONFIG_FILE.absolute()))
        
        # 设置按钮
        self.yesButton.setText(self.tr("Close"))
        self.cancelButton.hide()

        # 设置对话框大小和滚动区域
        self.widget.setFixedSize(600, 600)

        # 设置主布局边距为0，为滚动区域让路
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        # 创建滚动区域 - 使用ScrollArea（与settings界面一致）
        # ScrollArea使用SmoothScrollDelegate，在Mac触控板上性能更好
        # 而SingleDirectionScrollArea会导致向上滚动卡顿
        self.scroller = ScrollArea(self)
        self.scroller.setWidgetResizable(True)
        self.scroller.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.viewLayout.addWidget(self.scroller)

        # 创建滚动内容容器
        self.scroll_widget = QWidget(self)
        self.scroll_widget.setStyleSheet("QWidget { background: transparent; }")
        self.scroller.setWidget(self.scroll_widget)

        # 创建内容布局
        self.content_layout = QVBoxLayout(self.scroll_widget)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(12)

        # 标题
        self.titleLabel = SubtitleLabel(self.tr("Translation Task Settings"), self)
        self.content_layout.addWidget(self.titleLabel)
        
        # 初始化控件引用
        self.platform_combo = None
        self.split_mode_combo = None
        self.token_limit_card = None
        self.count_limit_card = None
        self.token_reserve_card = None
        self.is_api_platform = False
        
        
        # 创建设置卡片组
        self.create_platform_group()
        self.create_task_group()
        self.create_performance_group()
        
        # 根据平台类型更新 UI
        self.is_api_platform = self.check_if_api_platform()
        self.update_ui_by_platform_type()

        # 添加伸缩空间确保所有内容都能正确显示
        self.content_layout.addStretch(1)

        # 设置对话框宽度
        self.widget.setMinimumWidth(600)

    def create_platform_group(self):
        """创建平台选择组"""
        group = SettingCardGroup(self.tr("Translation Provider"), self)
        
        # 平台选择卡片
        platforms = self.platforms_config.get("platforms", {})
        platform_names = []
        self.platform_tags = []
        
        for tag, platform in platforms.items():
            platform_names.append(platform.get("name", tag))
            self.platform_tags.append(tag)

        platform_card = SettingCard(
            FluentIcon.GLOBE,
            self.tr("Current Provider"),
            self.tr("Select the translation provider for tasks"),
            group
        )
        
        self.platform_combo = ComboBox(platform_card)
        self.platform_combo.addItems(platform_names)
        
        # 设置当前选中（从appConfig读取）
        trans_platform = appConfig.trans_platform.value
        try:
            index = self.platform_tags.index(trans_platform)
            self.platform_combo.setCurrentIndex(index)
        except ValueError:
            self.platform_combo.setCurrentIndex(0)
        
        # 连接信号
        self.platform_combo.currentTextChanged.connect(self._on_platform_changed)
        
        platform_card.hBoxLayout.addWidget(self.platform_combo, 0, Qt.AlignmentFlag.AlignRight)
        platform_card.hBoxLayout.addSpacing(16)
        
        group.addSettingCard(platform_card)
        self.content_layout.addWidget(group)

    def create_task_group(self):
        """创建任务配置组"""
        group = SettingCardGroup(self.tr("Task Configuration"), self)
        
        # 任务切分模式
        split_mode_card = SettingCard(
            FluentIcon.TILES,
            self.tr("Task Split Mode"),
            self.tr("Select how to split tasks: by Token count or by entry count"),
            group
        )
        self.split_mode_combo = ComboBox(split_mode_card)
        self.split_mode_combo.addItems([self.tr("Token Mode"), self.tr("Entry Count Mode")])
        current_mode = appConfig.task_split_mode.value
        self.split_mode_combo.setCurrentIndex(0 if current_mode == "token" else 1)
        self.split_mode_combo.currentTextChanged.connect(self._on_split_mode_changed)
        split_mode_card.hBoxLayout.addWidget(self.split_mode_combo, 0, Qt.AlignmentFlag.AlignRight)
        split_mode_card.hBoxLayout.addSpacing(16)
        group.addSettingCard(split_mode_card)
        
        # AI提示词
        prompt_card = ExpandSettingCard(
            FluentIcon.EDIT,
            self.tr("AI Prompt"),
            self.tr("System prompt for AI translation"),
            group
        )
        self.prompt_edit = PlainTextEdit()
        self.prompt_edit.setPlainText(appConfig.task_prompt.value)
        self.prompt_edit.setMaximumHeight(150)
        self.prompt_edit.textChanged.connect(lambda: appConfig.set(appConfig.task_prompt, self.prompt_edit.toPlainText()))
        prompt_card.viewLayout.addWidget(self.prompt_edit)
        group.addSettingCard(prompt_card)
        
        # Token 上限
        self.token_limit_card = SettingCard(
            FluentIcon.TAG,
            self.tr("Task Token Limit"),
            self.tr("Maximum tokens per batch when using Token Mode"),
            group
        )
        token_limit_spin = SpinBox(self.token_limit_card)
        token_limit_spin.setRange(100, 200000)
        token_limit_spin.setSingleStep(100)
        token_limit_spin.setValue(appConfig.task_split_token_limit.value)
        token_limit_spin.setMinimumWidth(120)
        token_limit_spin.valueChanged.connect(lambda v: appConfig.set(appConfig.task_split_token_limit, v))
        self.token_limit_card.hBoxLayout.addWidget(token_limit_spin, 0, Qt.AlignmentFlag.AlignRight)
        self.token_limit_card.hBoxLayout.addSpacing(16)
        group.addSettingCard(self.token_limit_card)
        
        # 词条数上限
        self.count_limit_card = SettingCard(
            FluentIcon.MENU,
            self.tr("Entry Count Limit"),
            self.tr("Maximum entries per batch when using Entry Count Mode"),
            group
        )
        count_limit_spin = SpinBox(self.count_limit_card)
        count_limit_spin.setRange(1, 500)
        count_limit_spin.setValue(appConfig.task_split_count_limit.value)
        count_limit_spin.setMinimumWidth(120)
        count_limit_spin.valueChanged.connect(lambda v: appConfig.set(appConfig.task_split_count_limit, v))
        self.count_limit_card.hBoxLayout.addWidget(count_limit_spin, 0, Qt.AlignmentFlag.AlignRight)
        self.count_limit_card.hBoxLayout.addSpacing(16)
        group.addSettingCard(self.count_limit_card)
        
        # Token 预留
        self.token_reserve_card = SettingCard(
            FluentIcon.SAVE,
            self.tr("Token Reserve"),
            self.tr("Tokens reserved for model response"),
            group
        )
        token_reserve_spin = SpinBox(self.token_reserve_card)
        token_reserve_spin.setRange(0, 20000)
        token_reserve_spin.setSingleStep(128)
        token_reserve_spin.setValue(appConfig.task_token_reserve.value)
        token_reserve_spin.setMinimumWidth(120)
        token_reserve_spin.valueChanged.connect(lambda v: appConfig.set(appConfig.task_token_reserve, v))
        self.token_reserve_card.hBoxLayout.addWidget(token_reserve_spin, 0, Qt.AlignmentFlag.AlignRight)
        self.token_reserve_card.hBoxLayout.addSpacing(16)
        group.addSettingCard(self.token_reserve_card)
        
        self.content_layout.addWidget(group)

    def create_performance_group(self):
        """创建性能配置组"""
        group = SettingCardGroup(self.tr("Performance Settings"), self)
        
        # 并发任务数
        concurrency_card = SettingCard(
            FluentIcon.SPEED_OFF,
            self.tr("Concurrency"),
            self.tr("Parallel requests count. 0 = auto"),
            group
        )
        concurrency_spin = SpinBox(concurrency_card)
        concurrency_spin.setRange(0, 100)
        concurrency_spin.setValue(appConfig.task_concurrency.value)
        concurrency_spin.setMinimumWidth(120)
        concurrency_spin.valueChanged.connect(lambda v: appConfig.set(appConfig.task_concurrency, v))
        concurrency_card.hBoxLayout.addWidget(concurrency_spin, 0, Qt.AlignmentFlag.AlignRight)
        concurrency_card.hBoxLayout.addSpacing(16)
        group.addSettingCard(concurrency_card)
        
        # 请求超时
        timeout_card = SettingCard(
            FluentIcon.CERTIFICATE,
            self.tr("Request Timeout (s)"),
            self.tr("Maximum wait time for response"),
            group
        )
        timeout_spin = SpinBox(timeout_card)
        timeout_spin.setRange(10, 3600)
        timeout_spin.setSingleStep(10)
        timeout_spin.setValue(appConfig.task_request_timeout.value)
        timeout_spin.setMinimumWidth(120)
        timeout_spin.valueChanged.connect(lambda v: appConfig.set(appConfig.task_request_timeout, v))
        timeout_card.hBoxLayout.addWidget(timeout_spin, 0, Qt.AlignmentFlag.AlignRight)
        timeout_card.hBoxLayout.addSpacing(16)
        group.addSettingCard(timeout_card)
        
        # 最大轮次
        max_rounds_card = SettingCard(
            FluentIcon.UPDATE,
            self.tr("Max Rounds"),
            self.tr("Retry rounds for untranslated entries"),
            group
        )
        max_rounds_spin = SpinBox(max_rounds_card)
        max_rounds_spin.setRange(1, 50)
        max_rounds_spin.setValue(appConfig.task_max_rounds.value)
        max_rounds_spin.setMinimumWidth(120)
        max_rounds_spin.valueChanged.connect(lambda v: appConfig.set(appConfig.task_max_rounds, v))
        max_rounds_card.hBoxLayout.addWidget(max_rounds_spin, 0, Qt.AlignmentFlag.AlignRight)
        max_rounds_card.hBoxLayout.addSpacing(16)
        group.addSettingCard(max_rounds_card)
        
        self.content_layout.addWidget(group)

    def _on_platform_changed(self, text: str):
        """平台变更回调"""
        index = self.platform_combo.currentIndex()
        if index >= 0 and index < len(self.platform_tags):
            selected_tag = self.platform_tags[index]
            
            # 保存选中的平台到appConfig
            appConfig.set(appConfig.trans_platform, selected_tag)
            
            # 更新 UI
            self.is_api_platform = self.check_if_api_platform(selected_tag)
            self.update_ui_by_platform_type()
            
            InfoBar.success(
                self.tr("Success"),
                self.tr(f"Translation provider set to: {text}"),
                duration=2000,
                parent=self
            )

    def _on_split_mode_changed(self, text: str):
        """切分模式变更回调"""
        mode = "token" if text == self.tr("Token Mode") else "count"
        appConfig.set(appConfig.task_split_mode, mode)
        self.update_limit_cards_visibility()

    def check_if_api_platform(self, platform_tag=None):
        """检查指定平台是否为 API 类型（google/deepl）"""
        if not platform_tag:
            platform_tag = appConfig.trans_platform.value
        if not platform_tag:
            return False
        
        platforms = self.platforms_config.get("platforms", {})
        platform = platforms.get(platform_tag, {})
        return platform.get("group") == "api"
    
    def update_ui_by_platform_type(self):
        """根据平台类型更新 UI 显示"""
        if self.is_api_platform:
            # API 平台：强制使用词条数模式
            if self.split_mode_combo:
                self.split_mode_combo.setEnabled(False)
                self.split_mode_combo.setCurrentIndex(1)  # Entry Count Mode
            if self.token_limit_card:
                self.token_limit_card.hide()
            if self.token_reserve_card:
                self.token_reserve_card.hide()
            if self.count_limit_card:
                self.count_limit_card.show()
            
            # 强制设置为词条数模式
            if appConfig.task_split_mode.value != "count":
                appConfig.set(appConfig.task_split_mode, "count")
        else:
            # AI 平台：显示完整配置
            if self.split_mode_combo:
                self.split_mode_combo.setEnabled(True)
            if self.token_reserve_card:
                self.token_reserve_card.show()
            self.update_limit_cards_visibility()


    def update_limit_cards_visibility(self):
        """根据当前模式更新限制卡片的可见性"""
        if appConfig.task_split_mode.value == "count":
            if self.token_limit_card:
                self.token_limit_card.hide()
            if self.count_limit_card:
                self.count_limit_card.show()
        else:
            if self.count_limit_card:
                self.count_limit_card.hide()
            if self.token_limit_card:
                self.token_limit_card.show()
