import os

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QGridLayout, QFormLayout, QDialog, QFileDialog, \
    QMessageBox
from qfluentwidgets import ComboBoxSettingCard, FluentIcon as FIF, PushButton, CardWidget, SimpleCardWidget
from app.common.constant import LANGUAGES, ActionType
from app.common.config import cfg
from app.view.components.drop_area import DropArea
from app.common.utils.notify_util import notify_common_error, notify_error
from app.common.utils.file_util import get_all_json_files, get_dict_path, get_error_dict_path
from app.view.components.progress_bar import CustomProgressBar
from app.core import action


def handle_action(folder_path: str, action_type: ActionType):
    """
    Execute action on the mod folder using appropriate handler

    Args:
        folder_path: Path to the mod folder
        action_type: Action to perform
    """
    try:
        if action_type == ActionType.EXTRACT:
            action.extract(folder_path)
        elif action_type == ActionType.GENERATE:
            action.generate(folder_path)
        elif action_type == ActionType.VALIDATE:
            action.validate(folder_path)
        elif action_type == ActionType.IMPORT_ERROR:
            action.import_from_error(folder_path)
    except Exception as e:
        notify_error(e, folder_path)


class TranslationThread(QThread):
    progress_signal = Signal(int)
    total_entries_signal = Signal(int)
    error_signal = Signal(str)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.running = True

    def run(self):
        self.progress_signal.emit(0)
        batch_size = 1
        if cfg.trans_model.value != "google" and cfg.trans_model.value != "deepl":
            batch_size = cfg.ai_batch_size.value
        try:
            action.translate(self.folder_path, self, batch_size)
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
            action.process_old_common(self.parent().drop_area.folderPath, self.old_folder_path,
                                      self.translated_folder_path)
        else:
            notify_common_error(self.tr("Notice"), self.tr("Please select both folders"))
        self.close()


class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.translation_thread = None
        self.layout = QVBoxLayout(self)

        # 创建源语言和目标语言选择器
        self.source_language = ComboBoxSettingCard(
            configItem=cfg.source_language,
            icon=FIF.PLAY,
            title=self.tr('From'),
            content=self.tr('Select source language'),
            texts=list(LANGUAGES.keys()),
            parent=self
        )

        self.to_language = ComboBoxSettingCard(
            configItem=cfg.to_language,
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
            (self.tr("Translate"), self.translate_action, (1, 0)),
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

        # 添加进度条
        self.progress_bar = CustomProgressBar(self)

        self.__initWidget()

    def __initWidget(self):
        self.setObjectName("homeInterface")
        self.layout.addWidget(self.source_language)
        self.layout.addWidget(self.to_language)
        self.layout.addWidget(self.drop_area)
        self.layout.addWidget(self.button_group_box)
        self.layout.addWidget(self.progress_bar)

        # self.layout.addStretch(1)

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

        if cfg.trans_model.value != "google" and cfg.api_key.value == "":
            notify_common_error(self.tr("No api key"), self.tr("Please input api key config"))
            return

        translate_button = self.action_buttons[self.tr("Translate")]
        translate_button.setText(self.tr("Stop"))
        translate_button.clicked.disconnect()
        translate_button.clicked.connect(self.stop_translation)

        self.translation_thread = TranslationThread(self.drop_area.folderPath)
        self.translation_thread.progress_signal.connect(self.progress_bar.setValue)
        self.translation_thread.total_entries_signal.connect(self.progress_bar.setMaximum)
        self.translation_thread.finished.connect(self.on_translation_finished)
        self.translation_thread.error_signal.connect(self.on_translation_error)
        self.translation_thread.start()

    def on_translation_finished(self):
        translate_button = self.action_buttons[self.tr("Translate")]
        translate_button.setText(self.tr("Translate"))
        translate_button.clicked.disconnect()
        translate_button.clicked.connect(self.translate_action)

    def stop_translation(self):
        self.translation_thread.running = False

    def on_translation_error(self, error_message):
        QMessageBox.critical(self, self.tr("Translation Error"), error_message)
