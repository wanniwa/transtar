import os
import threading
import traceback

import wjson
from rich import print
from PySide6.QtCore import Qt
from qfluentwidgets import InfoBar
from qfluentwidgets import InfoBarPosition

from app.core.EventManager import EventManager
from app.common.setting import TRANS_CONFIG_FILE,DEBUG
from app.common.config import appConfig


# 事件列表
class Event:
    API_TEST_DONE = 100  # API 测试完成
    API_TEST_START = 101  # API 测试开始
    TASK_START = 210  # 翻译开始
    TASK_UPDATE = 220  # 翻译状态更新
    TASK_STOP = 230  # 翻译停止
    TASK_STOP_DONE = 231  # 翻译停止完成
    TASK_COMPLETED = 232  # 翻译完成

    TASK_CONTINUE_CHECK = 240  # 继续翻译状态检查
    TASK_CONTINUE_CHECK_DONE = 241  # 继续翻译状态检查完成
    TASK_MANUAL_EXPORT = 250  # 翻译结果手动导出
    CACHE_FILE_AUTO_SAVE = 300  # 缓存文件自动保存

    APP_UPDATE_CHECK: int = 600  # 检查更新
    APP_UPDATE_CHECK_DONE: int = 610  # 检查更新完成
    APP_UPDATE_DOWNLOAD: int = 620  # 下载应用
    APP_UPDATE_DOWNLOAD_UPDATE: int = 630  # 下载应用更新

    GLOSS_TASK_START = 700  # 术语表翻译 开始
    GLOSS_TASK_DONE = 701  # 术语表翻译 完成

    TABLE_TRANSLATE_START = 800  # 表格翻译 开始
    TABLE_TRANSLATE_DONE = 801  # 表格翻译 完成
    TABLE_POLISH_START = 810  # 表格润色 开始
    TABLE_POLISH_DONE = 811  # 表格润色 完成
    TABLE_FORMAT_START = 820  # 表格排版 开始
    TABLE_FORMAT_DONE = 821  # 表格排版 完成

    TERM_EXTRACTION_START = 830  # 术语提取开始
    TERM_EXTRACTION_DONE = 831

    TERM_TRANSLATE_SAVE_START = 832  # 实体提取开始
    TERM_TRANSLATE_SAVE_DONE = 833

    TRANSLATION_CHECK_START = 840  # 语言检查开始

    TABLE_UPDATE = 898  # 表格更新
    TABLE_FORMAT = 899  # 表格重排

    APP_SHUT_DOWN = 99999  # 应用关闭


# 软件运行状态列表
class Status():
    IDLE = 1000  # 无任务
    TASKING = 1001  # 任务中
    STOPING = 1002  # 停止中
    TASKSTOPPED = 1003  # 任务已停止

    API_TEST = 2000  # 接口测试中
    GLOSS_TASK = 3000  # 术语表翻译中
    TABLE_TASK = 4001  # 表格任务中


class TransBase():
    # 事件列表
    EVENT = Event()

    # 状态列表
    STATUS = Status()

    # 配置文件路径
    CONFIG_PATH = TRANS_CONFIG_FILE.absolute()

    # 类线程锁
    CONFIG_FILE_LOCK = threading.Lock()

    def __init__(self, *args, **kwargs) -> None:
        # 在多重继承中，正确调用 super().__init__()
        # 确保 QObject 等父类能够正确初始化
        # super().__init__()

        # 默认配置
        self.default = {}

        # 获取事件管理器单例
        self.event_manager_singleton = EventManager()

        # 类变量
        TransBase.work_status = TransBase.STATUS.IDLE if not hasattr(TransBase,
                                                                     "work_status") else TransBase.work_status

    def get_parent_window(self):
        """统一获取父窗口对象"""
        if hasattr(self, 'window'):
            if callable(self.window):
                return self.window()
            else:
                return self.window
        return None
    
    def is_debug(self) -> bool:
        """返回调试模式状态"""
        return DEBUG
        
        # INFO
    def info(self, msg: str) -> None:
        print(f"[[green]INFO[/]] {msg}")

        # ERROR

    def error(self, msg: str, e: Exception = None) -> None:
        if e is None:
            print(f"[[red]ERROR[/]] {msg}")
        else:
            tb_str = "".join(traceback.format_exception(None, e, e.__traceback__)).strip()
            print(f"[[red]ERROR[/]] {msg}\n{e}\n{tb_str}")

        # WARNING

    def warning(self, msg: str) -> None:
        print(f"[[red]WARNING[/]] {msg}")

    # Toast
    def info_toast(self, title: str, content: str) -> None:
        InfoBar.info(
            title=title,
            content=content,
            parent=self.get_parent_window(),
            duration=2500,
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.TOP,
            isClosable=True,
        )

    # Toast
    def error_toast(self, title: str, content: str) -> None:
        InfoBar.error(
            title=title,
            content=content,
            parent=self.get_parent_window(),
            duration=2500,
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.TOP,
            isClosable=True,
        )

    # Toast
    def success_toast(self, title: str, content: str) -> None:
        InfoBar.success(
            title=title,
            content=content,
            parent=self.get_parent_window(),
            duration=2500,
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.TOP,
            isClosable=True,
        )

    # Toast
    def warning_toast(self, title: str, content: str) -> None:
        InfoBar.warning(
            title=title,
            content=content,
            parent=self.get_parent_window(),
            duration=2500,
            orient=Qt.Orientation.Horizontal,
            position=InfoBarPosition.TOP,
            isClosable=True,
        )

    # 载入配置文件
    def load_config(self) -> dict:
        config = {}

        with TransBase.CONFIG_FILE_LOCK:
            if os.path.exists(TransBase.CONFIG_PATH):
                with open(TransBase.CONFIG_PATH, "r", encoding="utf-8") as reader:
                    config = wjson.load(reader)
            else:
                self.warning("配置文件不存在 ...")

        return config

    # 保存配置文件
    def save_config(self, new: dict) -> None:
        old = {}

        # 读取配置文件
        with TransBase.CONFIG_FILE_LOCK:
            if os.path.exists(TransBase.CONFIG_PATH):
                with open(TransBase.CONFIG_PATH, "r", encoding="utf-8") as reader:
                    old = wjson.load(reader)

        # 对比新旧数据是否一致，一致则跳过后续步骤
        # 当字典中包含子字典或子列表时，使用 == 运算符仍然可以进行比较
        # Python 会递归地比较所有嵌套的结构，确保每个层次的键值对都相等
        if old == new:
            return old

        # 更新配置数据
        for k, v in new.items():
            if k not in old.keys():
                old[k] = v
            else:
                old[k] = new[k]

        # 写入配置文件
        with TransBase.CONFIG_FILE_LOCK:
            # 确保配置文件目录存在
            os.makedirs(os.path.dirname(TransBase.CONFIG_PATH), exist_ok=True)
            with open(TransBase.CONFIG_PATH, "w", encoding="utf-8") as writer:
                writer.write(wjson.dumps(old))
        return old

    # 更新合并配置
    def fill_config(self, old: dict, new: dict) -> dict:

        """深度合并字典"""
        for k, v in new.items():
            if isinstance(v, dict) and k in old:
                # 递归合并子字典
                old[k] = self.fill_config(old[k], v)
            elif k not in old:
                old[k] = v
        return old

        """合并字典"""
        for k, v in new.items():
            if k not in old.keys():
                old[k] = v

        return old

    # 用默认值更新并加载配置文件
    def load_config_from_default(self) -> dict:
        # 1. 加载已有配置
        config = self.load_config()  # 从文件读取用户配置

        # 2. 合并默认配置
        config = self.fill_config(
            old=config,  # 用户现有配置
            new=getattr(self, "default", {})  # 当前类的默认配置
        )

        # 3. 返回合并结果
        return config
        # PRINT

    def print(self, msg: str) -> None:
        print(msg)

    # 触发事件
    def event_emit(self, event: int, data: dict) -> None:
        EventManager.get_singleton().emit(event, data)

    # 订阅事件
    def subscribe(self, event: int, hanlder: callable) -> None:
        EventManager.get_singleton().subscribe(event, hanlder)

    # 取消订阅事件
    def unsubscribe(self, event: int, hanlder: callable) -> None:
        EventManager.get_singleton().unsubscribe(event, hanlder)

    def tra(self, str: str):
        return str
