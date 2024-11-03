import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QGridLayout, QFormLayout, QDialog, QFileDialog, \
    QProgressBar
from qfluentwidgets import ComboBoxSettingCard, FluentIcon as FIF, PushButton, Dialog, ProgressBar
from app.common.constant import LANGUAGES
from app.common.config import cfg
from app.view.components.drop_area import DropArea
from app.common.utils.dialog_utils import notify_common_error

def process_folder(folder_path, action_type):
    pass
    # if folder_path:
    #     try:
    #         if action_type == 1 or action_type == 2:
    #             # translation_module.process_common(folder_path, action_type)
    #         elif action_type == 3:
    #             translation_module.process_error(folder_path)
    #     except Exception as e:
    #         print(e)
    #         notify_error(e, folder_path)
    # else:
    #     notify_common_error("No mod folder selected", "Please select a folder to extract", "")


class ExtractOldDialog(QDialog):
    def __init__(self, parent=None):
        super(ExtractOldDialog, self).__init__(parent)

        self.old_folder_path = None
        self.translated_folder_path = None
        self.setWindowTitle(self.tr("Extract Old"))
        self.setFixedWidth(400)

        self.layout = QFormLayout()

        self.old_folder_selector = PushButton(self.tr("Select old mod folder"))
        self.old_folder_selector.clicked.connect(self.select_old_folder)
        self.layout.addRow(self.old_folder_selector)

        self.translated_folder_selector = PushButton(self.tr("Select translated mod folder"))
        self.translated_folder_selector.clicked.connect(self.select_translated_folder)
        self.layout.addRow(self.translated_folder_selector)

        self.execute_button = PushButton(self.tr("Execute"))
        self.execute_button.clicked.connect(self.execute_action)
        self.layout.addRow(self.execute_button)

        self.setLayout(self.layout)

    def select_old_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.tr("Select Old Mod Folder"))
        if folder_path:
            self.old_folder_path = folder_path
            self.old_folder_selector.setText(folder_path)

    def select_translated_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.tr("Select Translated Mod Folder"))
        if folder_path:
            self.translated_folder_path = folder_path
            self.translated_folder_selector.setText(folder_path)

    def execute_action(self):
        pass
        # if self.old_folder_path is not None and self.translated_folder_path is not None:
        #     translation_module.process_old_common(self.parent().drop_area.folderPath, self.old_folder_path,
        #                                           self.translated_folder_path)
        # else:
        #     notify_common_error("Notice", "Please select both folders", "")
        # self.close()

class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.layout = QVBoxLayout(self)

        # 创建源语言和目标语言选择器
        self.from_language = ComboBoxSettingCard(
            configItem=cfg.from_language,
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
        for combo in [self.from_language.comboBox, self.to_language.comboBox]:
            for i, code in enumerate(LANGUAGES.values()):
                combo.setItemData(i, code)

        # 文件夹拖拽区域
        self.drop_area = DropArea(self, self.tr("Drop folder here or click to select"))

        # 创建一个QGroupBox
        self.button_group_box = QGroupBox()
        button_group_box_layout = QGridLayout(self.button_group_box)

        # 按钮信息列表，包含文本、事件和位置
        button_info = [
            ("Extract", self.extract_action, (0, 0)),  # 第一行第一列
            ("Extract old", self.extract_old_action, (0, 1)),  # 第一行第二列
            ("Translate", self.translate_action, (1, 0)),  # 第二行第一列
            ("Validate", self.validate_action, (2, 0)),  # 第二行第二列
            ("Import from error", self.import_from_error, (2, 1)),  # 第三行第一列
            ("Generate", self.generate_action, (3, 0)),  # 第三行第二列
        ]

        # 创建按钮并添加到布局中
        for text, action, position in button_info:
            button = PushButton(self.tr(text), self)
            button.clicked.connect(action)
            button_group_box_layout.addWidget(button, position[0], position[1])  # 使用自定义位置

        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v/%m")
        self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #D3D3D3;  /* Light gray border color */
                    border-radius: 5px;
                    text-align: center;
                }
            """)

        self.__initWidget()

    def __initWidget(self):
        self.setObjectName("homeInterface")
        self.layout.addWidget(self.from_language)
        self.layout.addWidget(self.to_language)
        self.layout.addWidget(self.drop_area)
        self.layout.addWidget(self.button_group_box)
        self.layout.addWidget(self.progress_bar)

        # self.layout.addStretch(1)

    def extract_action(self):
        if self.drop_area.folderPath:
            process_folder(self.drop_area.folderPath, 1)
        else:
            notify_common_error(self.parent(), 
                              self.tr("No folder selected"), 
                              self.tr("Please select a folder to generate"))

    def extract_old_action(self):
        if self.drop_area.folderPath:
            dialog = ExtractOldDialog(self)
            dialog.exec()
        else:
            notify_common_error(self.parent(),
                              self.tr("No folder selected"),
                              self.tr("Please select a folder"))

    def generate_action(self):
        if self.drop_area.folderPath:
            process_folder(self.drop_area.folderPath, 2)
        else:
            notify_common_error(self.parent(),
                              self.tr("No folder selected"),
                              self.tr("Please select a folder to generate"))

    def validate_action(self):
        if self.drop_area.folderPath:
            if os.path.exists(self.drop_area.folderPath + " dict"):
                process_folder(self.drop_area.folderPath, 3)
            else:
                notify_common_error(self.parent(),
                                  self.tr("No dict folder"),
                                  self.tr("Please select a folder to generate"))
        else:
            notify_common_error(self.parent(),
                              self.tr("No folder selected"),
                              self.tr("Please select a folder to validate"))

    def import_from_error(self):
        if self.drop_area.folderPath:
            if os.path.exists(self.drop_area.folderPath + " dict"):
                pass
            else:
                notify_common_error(self.parent(),
                                  self.tr("No dict folder"),
                                  self.tr("Please select a folder to generate"))
        else:
            notify_common_error(self.parent(),
                              self.tr("No folder selected"),
                              self.tr("Please select a folder to import"))

    def translate_action(self):
        pass
        # if self.drop_area.folderPath:
        #     if os.path.exists(self.drop_area.folderPath + " dict"):
        #         json_files = translation_module.get_all_json_files(
        #             translation_module.get_dict_path(self.drop_area.folderPath))
        #         if len(json_files) == 0:
        #             notify_common_error("No dict files", "Please generate dict files first", "")
        #             return
        #         config = get_config()
        #         if config["model"] != "google" and config["api_key"] == "":
        #             notify_common_error("No api key", "Please input api key config", "")
        #             return
        #
        #         self.translate_button.setText("Stop")
        #         self.translate_button.clicked.disconnect()  # 断开原有的点击事件
        #         self.translate_button.clicked.connect(self.stop_translation)  #
        #         self.translation_thread = TranslationThread(self.drop_area.folderPath, 4)
        #         self.translation_thread.progress_signal.connect(self.progress_bar.setValue)
        #         self.translation_thread.total_entries_signal.connect(self.progress_bar.setMaximum)  # 连接新的信号到新的槽函数
        #         self.translation_thread.finished.connect(self.on_translation_finished)  # 连接线程完成信号到新的槽函数
        #         self.translation_thread.error_signal.connect(self.on_translation_error)  # 连接错误信号到新的槽函数
        #         self.translation_thread.start()
        #     else:
        #         notify_common_error("No dict folder", "Please select a folder to generate", "")
        # else:
        #     notify_common_error("No folder selected", "Please select a folder to translate", "")