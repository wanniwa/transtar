# coding:utf-8
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import QWidget, QLabel
from qfluentwidgets import FluentIcon as FIF, OptionsSettingCard, RangeSettingCard
from qfluentwidgets import InfoBar
from qfluentwidgets import SettingCardGroup as CardGroup
from qfluentwidgets import (SwitchSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout,
                            setTheme, setFont)

from .components.setting_card import LineEditSettingCard, TextEditSettingCard
from ..common.config import cfg,models
from ..common.setting import HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet


class SettingCardGroup(CardGroup):

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        setFont(self.titleLabel, 14, QFont.Weight.DemiBold)


class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        self.translationGroup = SettingCardGroup(
            self.tr('Translation'), self.scrollWidget)

        self.i18n_ignore_cp_card = SwitchSettingCard(
            FIF.FLAG,
            self.tr('Extract CP file'),
            self.tr('CP files will translated when i18n files exist.'),
            configItem=cfg.i18n_ignore_cp,
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
        self.ai_batch_size = RangeSettingCard(
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
            self.tr('Please enter the prompt word. If empty, the default prompt will be used. like: You are currently a professional Stardew Valley mod translator.'),
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

        # # update software
        # self.updateSoftwareGroup = SettingCardGroup(
        #     self.tr("Software update"), self.scrollWidget)
        # self.updateOnStartUpCard = SwitchSettingCard(
        #     FIF.UPDATE,
        #     self.tr('Check for updates when the application starts'),
        #     self.tr('The new version will be more stable and have more features'),
        #     configItem=cfg.checkUpdateAtStartUp,
        #     parent=self.updateSoftwareGroup
        # )

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

        self.translationGroup.addSettingCard(self.i18n_ignore_cp_card)
        self.translationGroup.addSettingCard(self.i18n_from_language_json_card)
        self.translationGroup.addSettingCard(self.trans_mode_card)
        self.translationGroup.addSettingCard(self.api_key_card)
        self.translationGroup.addSettingCard(self.ai_batch_size)
        self.translationGroup.addSettingCard(self.ai_prompt_card)

        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        # self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.translationGroup)
        self.expandLayout.addWidget(self.personalGroup)
        # self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)

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
        self.aboutCard.clicked.connect(signalBus.checkUpdateSig)

        # about
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
