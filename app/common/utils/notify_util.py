import logging

from qfluentwidgets import Dialog

from app.common.window_manager import get_window
from app.view.components.ErrorDialog import FileErrorDialog


def notify_common_error(title: str, content: str):
    """
    显示通用错误对话框
    Args:
        :param title: 标题
        :param content: 内容
    """
    msg = Dialog(title, content, get_window())
    msg.cancelButton.hide()
    msg.buttonLayout.insertStretch(1)
    msg.exec()


def notify_error(e, tb):
    logging.error(e, stacklevel=1, exc_info=True)
    msg = FileErrorDialog(e, tb, get_window())
    msg.exec()
