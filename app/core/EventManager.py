import threading
from PySide6.QtCore import Qt
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

class EventManager(QObject):

    # 单一实例
    _singleton = None
    _lock = threading.Lock()

    # 自定义信号
    # 字典类型或者其他复杂对象应该使用 object 作为信号参数类型，这样可以传递任意 Python 对象，包括 dict
    signal = Signal(int, object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signal.connect(self.process_event, Qt.ConnectionType.QueuedConnection)
        # 事件列表 - 移到实例变量
        self.event_callbacks = {}

    # 获取单例
    @staticmethod
    def get_singleton():
        if EventManager._singleton is None:
            with EventManager._lock:
                # 双重检查锁定模式
                if EventManager._singleton is None:
                    EventManager._singleton = EventManager()
        return EventManager._singleton

    # 处理事件
    def process_event(self, event: int, data: dict):
        if event in self.event_callbacks:
            for hanlder in self.event_callbacks[event]:
                hanlder(event, data)

    # 触发事件
    def emit(self, event: int, data: dict):
        self.signal.emit(event, data)

    # 订阅事件
    def subscribe(self, event: int, hanlder: callable):
        if event not in self.event_callbacks:
            self.event_callbacks[event] = []
        self.event_callbacks[event].append(hanlder)

    # 取消订阅事件
    def unsubscribe(self, event: int, hanlder: callable):
        if event in self.event_callbacks:
            self.event_callbacks[event].remove(hanlder)
