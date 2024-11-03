from qfluentwidgets import Dialog

def notify_common_error(parent, text, informative_text, detailed_text=""):
    """
    显示通用错误对话框
    
    Args:
        parent: 父窗口
        text: 主要错误信息（应该在调用前已经用tr处理）
        informative_text: 提示性文本（应该在调用前已经用tr处理）
        detailed_text: 详细信息（可选，应该在调用前已经用tr处理）
    """
    msg = Dialog(text, informative_text, parent)
    msg.cancelButton.hide()
    msg.buttonLayout.insertStretch(1)
    msg.exec() 