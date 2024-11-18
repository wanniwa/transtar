# coding: utf-8
from PySide6.QtCore import QUrl, QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QApplication

from qfluentwidgets import NavigationItemPosition, MSFluentWindow, SplashScreen, SplitFluentWindow, setThemeColor, \
    FluentThemeColor
from qfluentwidgets import FluentIcon as FIF

from .setting_interface import SettingInterface
from .home_interface import HomeInterface
from ..common.config import cfg
from ..common.icon import Icon
from ..common.signal_bus import signalBus
from ..common import resource
from qframelesswindow.utils import getSystemAccentColor

from ..common.window_manager import set_window


class MainWindow(MSFluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()
        set_window(self)

        setThemeColor(QColor('#edb007'))


        # TODO: create sub interface
        self.homeInterface = HomeInterface(self)
        self.settingInterface = SettingInterface(self)

        # add items to navigation interface
        self.initNavigation()

        # 如果启用了自动检查更新，延迟几秒后检查
        if cfg.checkUpdateAtStartUp.value:
            # 延迟3秒后检查更新，让主窗口完全加载
            QTimer.singleShot(3000, self._checkUpdate)

    def _checkUpdate(self):
        """检查更新"""
        signalBus.checkUpdateSig.emit(False)  # 启动时检查更新不显示"无更新"提示

    def initNavigation(self):
        # self.navigationInterface.setAcrylicEnabled(True)

        # TODO: add navigation items
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))

        # add custom widget to bottom
        self.addSubInterface(
            self.settingInterface, Icon.SETTINGS, self.tr('Settings'), Icon.SETTINGS_FILLED, NavigationItemPosition.BOTTOM)

        self.splashScreen.finish()

    def initWindow(self):
        # self.resize(760, 680)
        self.setFixedHeight(700)
        self.setFixedWidth(655)
        # self.setMinimumWidth(760)
        self.setWindowIcon(QIcon(':/app/images/logo.png'))
        self.setWindowTitle('Transtar')

        self.setCustomBackgroundColor(QColor(240, 244, 249), QColor(32, 32, 32))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())