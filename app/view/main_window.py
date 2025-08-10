# coding: utf-8
from PySide6.QtCore import QUrl, QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QApplication

from qfluentwidgets import NavigationItemPosition, MSFluentWindow, SplashScreen, SplitFluentWindow, setThemeColor, \
    FluentThemeColor, InfoBar, FluentWindow
from qfluentwidgets import FluentIcon as FIF

from .platform.PlatformInterface import PlatformInterface
from .setting_interface import SettingInterface
from .home_interface import HomeInterface
from ..common.config import appConfig
from ..common.icon import Icon
from ..common.signal_bus import signalBus
from ..common import resource
from qframelesswindow.utils import getSystemAccentColor

from ..common.window_manager import set_window
from .dict_interface import DictInterface
from .paratranz_interface import ParatranzInterface
from .local_dict_interface import LocalDictInterface


class MainWindow(FluentWindow):
    THEME_COLOR = '#edb007'
    APP_WIDTH = 1100
    APP_HEIGHT = 800

    def __init__(self):
        super().__init__()
        self.initWindow()
        set_window(self)

        setThemeColor(QColor(self.THEME_COLOR))

        # 设置侧边栏宽度
        self.navigationInterface.setExpandWidth(226)

        # 侧边栏默认展开
        # self.navigationInterface.setMinimumExpandWidth(self.APP_WIDTH)
        self.navigationInterface.expand(useAni=False)

        # 隐藏返回按钮
        self.navigationInterface.panel.setReturnButtonVisible(False)

        # add items to navigation interface
        self.initNavigation()

        # 延迟3秒后检查更新，让主窗口完全加载
        QTimer.singleShot(3000, self.check_for_updates)

    def check_for_updates(self):
        """检查更新"""
        if appConfig.checkUpdateAtStartUp.value:
            signalBus.checkUpdateSig.emit(False)  # 启动时检查更新不显示"无更新"提示

    def initNavigation(self):
        self.settingInterface = SettingInterface(self)
        self.homeInterface = HomeInterface(self)
        self.paratranzInterface = ParatranzInterface(self)
        self.localDictInterface = LocalDictInterface(self)
        self.platformInterface = PlatformInterface(self)

        # -------------------------SubInterface--------------------------
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))

        self.addSubInterface(self.platformInterface, FIF.IOT, self.tr('API Management'))

        self.addSubInterface(self.paratranzInterface, FIF.DICTIONARY, self.tr('Paratranz Dictionary'))
        # 获取 paratranzInterface 的导航项并重新绑定点击事件
        paratranzItem = self.navigationInterface.widget(self.paratranzInterface.objectName())
        if paratranzItem:
            # 断开原有的点击信号连接
            paratranzItem.clicked.disconnect()
            # 连接到我们的检查函数
            paratranzItem.clicked.connect(self.check_and_switch_to_paratranz)

        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('Application Settings'), NavigationItemPosition.BOTTOM)

        # # 添加本地字典界面
        # self.addSubInterface(
        #     self.localDictInterface,
        #     FIF.LIBRARY,
        #     self.tr('Local Dict'),
        #     position=NavigationItemPosition.TOP
        # )

        # 监听界面切换
        # self.stackedWidget.currentChanged.connect(self.handle_interface_changed)
        self.splashScreen.finish()

    # def handle_interface_changed(self, index: int):
    #     """处理界面切换"""
    #     current_widget = self.stackedWidget.widget(index)
    #     if isinstance(current_widget, HomeInterface):
    #         self.resize(655, 700)
    #     elif isinstance(current_widget, SettingInterface):
    #         self.resize(800, 800)
    #     else:
    #         self.resize(1100, 700)

    def initWindow(self):
        self.setMinimumSize(self.APP_WIDTH, self.APP_HEIGHT)

        self.resize(self.APP_WIDTH, self.APP_HEIGHT)  # 设置初始大小

        self.setWindowIcon(QIcon(':/app/images/logo.png'))
        self.setWindowTitle('Transtar')

        self.setCustomBackgroundColor(QColor(240, 244, 249), QColor(32, 32, 32))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def check_and_switch_to_paratranz(self):
        """检查是否选择了文件夹并切换到ParaTranz界面"""
        if not self.homeInterface.drop_area.folderPath:
            InfoBar.warning(
                self.tr('Warning'),
                self.tr('Please select a mod folder in Home page first'),
                duration=3000,
                parent=self
            )
            # 切换到主页
            self.stackedWidget.setCurrentWidget(self.homeInterface)
            return

        # 如果已选择文件夹，切换到ParaTranz界面
        self.stackedWidget.setCurrentWidget(self.paratranzInterface)

        # 刷新本地文件列表
        if hasattr(self.paratranzInterface, 'dictInterface'):
            self.paratranzInterface.dictInterface.refresh_local_files()
