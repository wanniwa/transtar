from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout

from .dict_interface import DictInterface 
from .paratranz_config_interface import ParatranzConfigInterface
from ..common.config import cfg


class ParatranzInterface(QWidget):
    """ ParaTranz界面,用于切换配置界面和字典界面 """
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('paratranzInterface')
        
        # 创建布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        
        # 创建堆叠窗口
        self.stackedWidget = QStackedWidget(self)
        
        # 创建配置界面和字典界面
        self.configInterface = ParatranzConfigInterface(self)
        self.dictInterface = DictInterface(self)
        
        # 添加界面到堆叠窗口
        self.stackedWidget.addWidget(self.configInterface) 
        self.stackedWidget.addWidget(self.dictInterface)
        
        # 添加到布局
        self.vBoxLayout.addWidget(self.stackedWidget)
        
        # 连接信号
        self.configInterface.configCompleted.connect(self.on_config_completed)

        # 初始化界面
        self.check_and_switch_interface()

    def check_and_switch_interface(self):
        """检查配置并切换到相应界面"""
        if cfg.paratranz_token.value and cfg.paratranz_project_id.value:
            self.stackedWidget.setCurrentWidget(self.dictInterface)
        else:
            self.stackedWidget.setCurrentWidget(self.configInterface)

    def on_config_completed(self):
        """配置完成时的处理"""
        if cfg.paratranz_token.value and cfg.paratranz_project_id.value:
            self.stackedWidget.setCurrentWidget(self.dictInterface)
            # 刷新字典界面
            self.dictInterface.refresh_files()

    def switch_to_config(self):
        """切换到配置界面"""
        self.stackedWidget.setCurrentWidget(self.configInterface)
        