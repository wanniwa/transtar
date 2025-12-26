import os

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QGridLayout, QFormLayout, QDialog, QFileDialog, \
    QMessageBox, QHBoxLayout
from qfluentwidgets import ComboBoxSettingCard, FluentIcon as FIF, PushButton, CardWidget, SimpleCardWidget, ToolButton
from app.common.constant import LANGUAGES, ActionType
from app.common.config import appConfig, load_config
from app.common.setting import TRANS_CONFIG_FILE
from app.core import Action
from app.view.components.DropArea import DropArea
from app.view.components.TaskSettingsDialog import TaskSettingsDialog
from app.view.components.TranslationDashboard import TranslationDashboard
from app.common.utils.notify_util import notify_common_error, notify_error
from app.common.utils.file_util import get_all_json_files, get_dict_path, get_error_dict_path
from app.view.components.ProgressBar import CustomProgressBar


def handle_action(folder_path: str, action_type: ActionType):
    """
    Execute action on the mod folder using appropriate handler

    Args:
        folder_path: Path to the mod folder
        action_type: Action to perform
    """
    try:
        if action_type == ActionType.EXTRACT:
            Action.extract(folder_path)
        elif action_type == ActionType.GENERATE:
            Action.generate(folder_path)
        elif action_type == ActionType.VALIDATE:
            Action.validate(folder_path)
        elif action_type == ActionType.IMPORT_ERROR:
            Action.import_from_error(folder_path)
    except Exception as e:
        print(e)
        notify_error(e, folder_path)


class TranslationThread(QThread):
    progress_signal = Signal(int)
    total_entries_signal = Signal(int)
    error_signal = Signal(str)
    # 新增：传递翻译配置信息
    config_signal = Signal(str, int)  # (platform_name, concurrency)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.running = True

    def run(self):
        self.progress_signal.emit(0)
        batch_size = 1  # google/deepl 使用单条翻译，AI模型在 Action.translate 内部自动批处理
        try:
            Action.translate(self.folder_path, self, batch_size)
        except Exception as e:
            print(e)
            self.error_signal.emit(str(e))

    def stop(self):
        self.running = False


class ExtractOldDialog(QDialog):
    def __init__(self, parent=None):
        super(ExtractOldDialog, self).__init__(parent)

        self.old_folder_path = None
        self.translated_folder_path = None
        self.setWindowTitle(self.tr("Extract Old"))
        self.setFixedWidth(400)

        self.layout = QFormLayout()

        self.old_folder_selector = PushButton()
        self.old_folder_selector.setText(self.tr("Select old mod folder"))
        self.old_folder_selector.clicked.connect(self.select_old_folder)
        self.layout.addRow(self.old_folder_selector)

        self.translated_folder_selector = PushButton()
        self.translated_folder_selector.setText(self.tr("Select translated mod folder"))
        self.translated_folder_selector.clicked.connect(self.select_translated_folder)
        self.layout.addRow(self.translated_folder_selector)

        self.execute_button = PushButton()
        self.execute_button.setText(self.tr("Execute"))
        self.execute_button.clicked.connect(self.execute_action)
        self.layout.addRow(self.execute_button)

        self.setLayout(self.layout)

    def select_old_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.tr("Select old mod folder"))
        if folder_path:
            self.old_folder_path = folder_path
            self.old_folder_selector.setText(folder_path)

    def select_translated_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.tr("Select translated mod folder"))
        if folder_path:
            self.translated_folder_path = folder_path
            self.translated_folder_selector.setText(folder_path)

    def execute_action(self):
        pass
        if self.old_folder_path is not None and self.translated_folder_path is not None:
            Action.process_old_common(self.parent().drop_area.folderPath, self.old_folder_path,
                                      self.translated_folder_path)
        else:
            notify_common_error(self.tr("Notice"), self.tr("Please select both folders"))
        self.close()


class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.translation_thread = None
        
        # 主布局改为水平布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧主内容区
        left_widget = QWidget(self)
        self.layout = QVBoxLayout(left_widget)

        # 创建源语言和目标语言选择器
        self.source_language = ComboBoxSettingCard(
            configItem=appConfig.source_language,
            icon=FIF.PLAY,
            title=self.tr('From'),
            content=self.tr('Select source language'),
            texts=list(LANGUAGES.keys()),
            parent=self
        )

        self.to_language = ComboBoxSettingCard(
            configItem=appConfig.to_language,
            icon=FIF.PLAY,
            title=self.tr('To'),
            content=self.tr('Select target language'),
            texts=list(LANGUAGES.keys()),
            parent=self
        )

        # 设置语言代码作为用户数据
        for combo in [self.source_language.comboBox, self.to_language.comboBox]:
            for i, code in enumerate(LANGUAGES.values()):
                combo.setItemData(i, code)

        # 文件夹拖拽区域
        self.drop_area = DropArea(self, self.tr("Drop folder here or click to select"))

        # 创建一个QGroupBox
        self.button_group_box = SimpleCardWidget()
        self.button_group_box.setFixedHeight(250)
        button_group_box_layout = QGridLayout(self.button_group_box)

        # 将按钮定义为实例变量
        self.action_buttons = {}

        # 按钮信息列表，包含文本、事件和位置
        button_info = [
            (self.tr("Extract"), self.extract_action, (0, 0)),
            (self.tr("Extract old"), self.extract_old_action, (0, 1)),
            (self.tr("Validate"), self.validate_action, (2, 0)),
            (self.tr("Import from error"), self.import_error, (2, 1)),
            (self.tr("Generate"), self.generate_action, (3, 0)),
        ]

        # 创建按钮并添加到布局中
        for text, bind_action, position in button_info:
            button = PushButton(text, self)
            button.clicked.connect(bind_action)
            button_group_box_layout.addWidget(button, position[0], position[1])
            # 将按钮保存到字典中
            self.action_buttons[text] = button

        # 翻译按钮
        translate_button = PushButton(self.tr("Translate"), self)
        translate_button.clicked.connect(self.translate_action)
        button_group_box_layout.addWidget(translate_button, 1, 0)
        self.action_buttons[self.tr("Translate")] = translate_button

        # 设置按钮（齿轮图标）
        settings_button = ToolButton(FIF.SETTING, self)
        settings_button.setToolTip(self.tr("Task Settings"))
        settings_button.clicked.connect(self.open_task_settings)
        button_group_box_layout.addWidget(settings_button, 1, 1)

        # 添加进度条
        self.progress_bar = CustomProgressBar(self)
        
        # 右侧翻译进度看板
        self.dashboard = TranslationDashboard(self)

        self.__initWidget(left_widget, main_layout)

    def __initWidget(self, left_widget, main_layout):
        self.setObjectName("homeInterface")
        self.layout.addWidget(self.source_language)
        self.layout.addWidget(self.to_language)
        self.layout.addWidget(self.drop_area)
        self.layout.addWidget(self.button_group_box)
        self.layout.addWidget(self.progress_bar)
        # self.layout.addStretch(1)
        
        # 将左侧内容区和右侧看板添加到主布局
        main_layout.addWidget(left_widget, stretch=1)
        main_layout.addWidget(self.dashboard, stretch=0)

    def extract_action(self):
        if not self.validate_folder_path():
            return
        handle_action(self.drop_area.folderPath, ActionType.EXTRACT)

    def validate_folder_path(self):
        if not self.drop_area.folderPath:
            notify_common_error(self.tr("No folder selected"), self.tr("Please select a folder"))
            return False
        return True

    def validate_dict_path(self):
        if not os.path.exists(self.drop_area.folderPath + " dict"):
            notify_common_error(self.tr("No dict folder"), self.tr("Please generate dict files first"))
            return False
        return True

    def extract_old_action(self):
        if not self.validate_folder_path():
            return
        dialog = ExtractOldDialog(self)
        dialog.exec()

    def generate_action(self):
        if not self.validate_folder_path():
            return
        handle_action(self.drop_area.folderPath, ActionType.GENERATE)

    def validate_action(self):
        if not self.validate_folder_path():
            return
        if not self.validate_dict_path():
            return
        handle_action(self.drop_area.folderPath, ActionType.VALIDATE)

    def import_error(self):
        if not self.validate_folder_path():
            return
        if not self.validate_dict_path():
            return
        handle_action(self.drop_area.folderPath, ActionType.IMPORT_ERROR)

    def translate_action(self):
        if not self.validate_folder_path():
            return
        if not self.validate_dict_path():
            return

        json_files = get_all_json_files(get_dict_path(self.drop_area.folderPath))
        if len(json_files) == 0:
            notify_common_error(self.tr("No dict files"), self.tr("Please generate dict files first"))
            return
        
        # 检查平台配置（除了 Google 以外都需要 API key）
        trans_platform = appConfig.trans_platform.value or "google"
        if trans_platform.lower() != "google":
            config = load_config(str(TRANS_CONFIG_FILE.absolute()))
            platforms = config.get("platforms", {})
            platform = platforms.get(trans_platform)
            
            if not platform:
                notify_common_error(
                    self.tr("Platform not found"),
                    self.tr(f"Platform '{trans_platform}' is not configured. Please configure it in the Platform page.")
                )
                return
            
            api_key = platform.get("api_key", "").strip()
            if not api_key:
                notify_common_error(
                    self.tr("API Key not configured"),
                    self.tr(f"Platform '{platform.get('name', trans_platform)}' requires an API key. Please configure it in the Platform page.")
                )
                return
        
        # 重置看板
        self.dashboard.reset()

        translate_button = self.action_buttons[self.tr("Translate")]
        translate_button.setText(self.tr("Stop"))
        translate_button.clicked.disconnect()
        translate_button.clicked.connect(self.stop_translation)

        self.translation_thread = TranslationThread(self.drop_area.folderPath)
        self.translation_thread.progress_signal.connect(self.progress_bar.setValue)
        self.translation_thread.progress_signal.connect(self.dashboard.update_progress)
        self.translation_thread.total_entries_signal.connect(self.progress_bar.setMaximum)
        self.translation_thread.total_entries_signal.connect(self.on_total_entries)
        self.translation_thread.config_signal.connect(self.on_translation_config)
        self.translation_thread.finished.connect(self.on_translation_finished)
        self.translation_thread.error_signal.connect(self.on_translation_error)
        self.translation_thread.start()

    def on_total_entries(self, total: int):
        """接收总条目数"""
        # 暂存总数，等待配置信息
        self.dashboard_total = total
    
    def on_translation_config(self, platform: str, concurrency: int):
        """接收翻译配置信息"""
        total = getattr(self, 'dashboard_total', 0)
        self.dashboard.start_translation(total, platform, concurrency)
    
    def on_translation_finished(self):
        translate_button = self.action_buttons[self.tr("Translate")]
        translate_button.setText(self.tr("Translate"))
        translate_button.clicked.disconnect()
        translate_button.clicked.connect(self.translate_action)
        
        # 完成看板
        self.dashboard.finish_translation()

    def stop_translation(self):
        self.translation_thread.running = False
        # 停止后保留看板数据，方便查看进度

    def on_translation_error(self, error_message):
        QMessageBox.critical(self, self.tr("Translation Error"), error_message)
        # 错误后保留看板数据，方便调试

    def open_task_settings(self):
        """打开任务设置对话框"""
        dialog = TaskSettingsDialog(self)
        dialog.exec()
