from qfluentwidgets import Dialog
from app.view.components.error_dailog import FileErrorDialog


def notify_common_error(title: str, content: str, parent):
    """
    显示通用错误对话框
    Args:
        :param title: 标题
        :param content: 内容
        :param parent: 父组件
    """
    msg = Dialog(title, content, parent)
    msg.cancelButton.hide()
    msg.buttonLayout.insertStretch(1)
    msg.exec()


def notify_error(e, tb):
    msg = FileErrorDialog(e, tb)
    msg.exec()
