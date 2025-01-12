# coding:utf-8
import platform
import subprocess
import traceback
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import QWidget, QLabel, QApplication
from packaging import version
from qfluentwidgets import FluentIcon as FIF, OptionsSettingCard, RangeSettingCard, MessageBox, InfoBar, StateToolTip
from qfluentwidgets import SettingCardGroup
from qfluentwidgets import (SwitchSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout,
                            setTheme, setFont)

from .components.check_update_thread import CheckUpdateThread
from .components.download_thread import DownloadThread
from .components.setting_card import LineEditSettingCard, TextEditSettingCard
from ..common.config import cfg, models
from ..common.setting import HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR, CONFIG_FOLDER
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..common.utils import file_util
from ..common.window_manager import get_window


class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.current_download_filename = None
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        self.translationGroup = SettingCardGroup(
            self.tr('Translation'), self.scrollWidget)

        self.i18n_extract_cp_card = SwitchSettingCard(
            FIF.FLAG,
            self.tr('Extract CP file'),
            self.tr('CP files will translated when i18n files exist.'),
            configItem=cfg.i18n_extract_cp,
            parent=self.translationGroup
        )
        self.i18n_from_language_json_card = SwitchSettingCard(
            FIF.FLAG,
            self.tr('Extract specified language'),
            self.tr('For example, replace default.json with zh.json'),
            configItem=cfg.i18n_source_flag,
            parent=self.translationGroup
        )
        self.trans_mode_card = OptionsSettingCard(
            cfg.trans_model,
            FIF.FLAG,
            self.tr('Trans model'),
            self.tr('Google、OpenAI……'),
            models,
            self.translationGroup
        )
        self.api_key_card = LineEditSettingCard(
            FIF.FLAG,
            self.tr('APIKEY'),
            self.tr('API Key for authentication.'),
            configItem=cfg.api_key,
            parent=self.translationGroup
        )
        self.ai_base_url_card = LineEditSettingCard(
            FIF.FLAG,
            self.tr('Base URL'),
            self.tr('Base URL for AI. If empty, use default URL.'),
            configItem=cfg.ai_base_url,
            parent=self.translationGroup
        )
        self.trans_custom_model_card = LineEditSettingCard(
            FIF.FLAG,
            self.tr('Trans custom model'),
            self.tr('Custom model for AI.'),
            configItem=cfg.trans_custom_model,
            parent=self.translationGroup
        )
        self.ai_batch_size_card = RangeSettingCard(
            cfg.ai_batch_size,
            FIF.FLAG,
            self.tr("AI batch size"),
            self.tr("Number of AI batch translate size."),
            parent=self.translationGroup
        )

        self.ai_prompt_card = TextEditSettingCard(
            FIF.FLAG,
            self.tr('AI prompt'),
            self.tr('Prompt get shown to the AI on all chat.'),
            self.tr(
                'Please enter the prompt word. If empty, the default prompt will be used. like: You are currently a professional Stardew Valley mod translator.'),
            configItem=cfg.ai_prompt,
            parent=self.translationGroup
        )

        # personalization
        self.personalGroup = SettingCardGroup(
            self.tr('Personalization'), self.scrollWidget)
        self.themeCard = ComboBoxSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('Application theme'),
            self.tr("Change the appearance of your application"),
            texts=[
                self.tr('Light'), self.tr('Dark'),
                self.tr('Use system setting')
            ],
            parent=self.personalGroup
        )
        self.zoomCard = ComboBoxSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("Use system setting")
            ],
            parent=self.personalGroup
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr('Language'),
            self.tr('Set your preferred language for UI'),
            texts=['简体中文', 'English', self.tr('Use system setting')],
            parent=self.personalGroup
        )

        # update software
        self.updateSoftwareGroup = SettingCardGroup(
            self.tr("Software update"), self.scrollWidget)
        self.updateOnStartUpCard = SwitchSettingCard(
            FIF.UPDATE,
            self.tr('Check for updates when the application starts'),
            self.tr('The new version will be more stable and have more features'),
            configItem=cfg.checkUpdateAtStartUp,
            parent=self.updateSoftwareGroup
        )

        # application
        self.aboutGroup = SettingCardGroup(self.tr('About'), self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr('Open help page'),
            FIF.HELP,
            self.tr('Help'),
            self.tr('Discover new features about Transtar'),
            self.aboutGroup
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('Provide feedback'),
            FIF.FEEDBACK,
            self.tr('Provide feedback'),
            self.tr('Help us improve Transtar by providing feedback'),
            self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('Check update'),
            FIF.INFO,
            self.tr('About'),
            '© ' + self.tr('Copyright') + f" {YEAR}, {AUTHOR}. " +
            self.tr('Version') + " " + VERSION,
            self.aboutGroup
        )
        self.openConfigCard = PrimaryPushSettingCard(
            self.tr('Open Config Folder'),
            FIF.FOLDER,
            self.tr('Config Folder'),
            self.tr('Open the configuration folder'),
            self.aboutGroup
        )

        # 添加检查更新线程
        self.check_update_thread = None

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 100, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')

        # initialize style sheet
        setFont(self.settingLabel, 23, QFont.Weight.DemiBold)
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)
        self.scrollWidget.setStyleSheet("QWidget{background:transparent}")

        # initialize layout
        self.__initLayout()
        self._connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 50)

        self.translationGroup.addSettingCard(self.i18n_extract_cp_card)
        self.translationGroup.addSettingCard(self.i18n_from_language_json_card)
        self.translationGroup.addSettingCard(self.trans_mode_card)
        self.translationGroup.addSettingCard(self.api_key_card)
        self.translationGroup.addSettingCard(self.ai_base_url_card)
        self.translationGroup.addSettingCard(self.trans_custom_model_card)
        self.translationGroup.addSettingCard(self.ai_batch_size_card)
        self.translationGroup.addSettingCard(self.ai_prompt_card)

        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)
        self.aboutGroup.addSettingCard(self.openConfigCard)

        # self.paratranzGroup.addSettingCard(self.paratranz_token_card)
        # self.paratranzGroup.addSettingCard(self.paratranz_project_id_card)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.translationGroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)
        # self.expandLayout.addWidget(self.paratranzGroup)

    def _showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=1500,
            parent=self
        )

    def _connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self._showRestartTooltip)

        # personalization
        cfg.themeChanged.connect(setTheme)

        # check update
        signalBus.checkUpdateSig.connect(self.check_for_updates)
        self.aboutCard.clicked.connect(lambda: signalBus.checkUpdateSig.emit(True))

        # about
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
        self.openConfigCard.clicked.connect(
            lambda: file_util.open_folder(str(CONFIG_FOLDER))
        )

    def check_for_updates(self, manual=True):
        # 禁用按钮并显示加载状态
        self.aboutCard.button.setEnabled(False)
        self.aboutCard.button.setText(self.tr("Checking..."))

        # 创建并启动检查更新线程
        self.check_update_thread = CheckUpdateThread()
        self.check_update_thread.finished_signal.connect(lambda success, data, error_msg:
                                                         self.handle_update_check_result(success, data, error_msg,
                                                                                         manual=manual))
        self.check_update_thread.start()

    def handle_update_check_result(self, success, data, error_msg, manual=False):
        # 恢复按钮状态
        self.aboutCard.button.setEnabled(True)
        self.aboutCard.button.setText(self.tr("Check update"))

        if success:
            try:
                latest_version = data.get('tag_name')
                current_version = VERSION

                if version.parse(latest_version) > version.parse(current_version):
                    w = MessageBox(
                        self.tr('Update Available'),
                        self.tr(
                            'Current version: {0}\nNew version: {1}\n\nDo you want to download the latest version?').format(
                            current_version, latest_version),
                        parent=get_window()
                    )

                    # 连接确认按钮的信号
                    w.yesButton.clicked.connect(
                        lambda: QDesktopServices.openUrl(
                            QUrl("https://www.nexusmods.com/stardewvalley/mods/20435?tab=files"))
                    )
                    # 连接确认按钮的信号到关闭对话框
                    w.yesButton.clicked.connect(w.close)
                    # 连接取消按钮的信号到关闭对话框
                    w.cancelButton.clicked.connect(w.close)

                    w.show()
                else:
                    # 只在手动检查时显示"已是最新版本"的提示
                    if manual:
                        message = self.tr("You are already using the latest version ({0})").format(current_version)
                        InfoBar.info(
                            self.tr("No Update"),
                            message,
                            duration=3000,
                            parent=get_window()
                        )
            except Exception as e:
                print(f"Handle update result error: {str(e)}")
                InfoBar.error(
                    self.tr("Update Check Failed"),
                    str(e),
                    duration=3000,
                    parent=get_window()
                )
        else:
            InfoBar.error(
                self.tr("Update Check Failed"),
                error_msg,
                duration=3000,
                parent=get_window()
            )

    def download_update(self, url):
        try:
            self.current_download_filename = url.split('/')[-1]  # 保存当前下载的文件名
            file_path = CONFIG_FOLDER / self.current_download_filename

            # 创建状态提示
            self.state_tooltip = StateToolTip(
                self.tr('Downloading Update'),
                self.tr('Downloading, please wait...'),
                parent=get_window()
            )
            self.state_tooltip.move(self.state_tooltip.getSuitablePos())
            self.state_tooltip.show()

            # 创建下载线程
            self.download_thread = DownloadThread(url, str(file_path))
            self.download_thread.progress_signal.connect(self.update_progress)
            self.download_thread.finished_signal.connect(self.download_finished)

            # 开始下载
            self.download_thread.start()

        except Exception as e:
            print(f"Download setup error: {str(e)}")
            print("Traceback:")
            print(traceback.format_exc())
            InfoBar.error(
                self.tr("Download Failed"),
                str(e),
                parent=get_window()
            )

    def update_progress(self, progress):
        """更新进度提示"""
        # 使用 tr 的二个参数传递变量
        message = self.tr('Downloading... {0}%').format(progress)
        self.state_tooltip.setContent(message)

    def download_finished(self, success, error_msg):
        """下载完成的处理"""
        self.state_tooltip.close()

        if success:
            file_path = CONFIG_FOLDER / self.current_download_filename

            if platform.system() == 'Windows' and file_path.suffix.lower() == '.exe':
                w = MessageBox(
                    self.tr('Installation'),
                    self.tr('Download completed. Do you want to install it now?'),
                    parent=get_window()
                )

                if w.exec():
                    try:
                        # Windows平台直接执行安装包并关闭程序
                        subprocess.Popen([str(file_path)], shell=True)
                        QApplication.quit()
                    except Exception as e:
                        print(f"Execute installer error: {str(e)}")
                        print("Traceback:")
                        print(traceback.format_exc())
                        # 如果执行失败，退回到打开文件夹
                        file_util.open_folder(str(CONFIG_FOLDER))
                        InfoBar.warning(
                            self.tr("Launch Failed"),
                            self.tr("Could not launch installer, opening download folder instead"),
                            duration=3000,
                            parent=get_window()
                        )
                else:
                    # 用户选择不立即安装，打开下载目录
                    file_util.open_folder(str(CONFIG_FOLDER))
                    InfoBar.success(
                        self.tr("Download Complete"),
                        self.tr("Update has been downloaded to AppData folder"),
                        duration=3000,
                        parent=get_window()
                    )
            else:
                InfoBar.success(
                    self.tr("Download Complete"),
                    self.tr("Update has been downloaded successfully"),
                    duration=3000,
                    parent=get_window()
                )
                # 非Windows平台或非exe文件，打开下载目录
                file_util.open_folder(str(CONFIG_FOLDER))
        else:
            InfoBar.error(
                self.tr("Download Failed"),
                error_msg,
                duration=3000,
                parent=get_window()
            )
