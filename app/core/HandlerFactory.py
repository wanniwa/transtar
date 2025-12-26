from typing import Dict, Type
from app.common.constant import FileType
from app.core.handlers.BaseTransHandler import BaseTransHandler
from app.core.handlers.CpHandler import CPTransHandler
from app.core.handlers.SimpleHandler import MailTransHandler, JATransHandler, BLTransHandler, STFTransHandler, \
    QFTransHandler
from app.core.handlers.I18nHandler import I18nTransHandler

UNKNOWN = "UNKNOWN"
JA = "JA.json"
CP = "CP.json"
I18N = "i18n.json"
MAIL = "mail.json"
BL = "BL.json"
STF = "STF.json"
QF = "QF.json"

class HandlerFactory:
    _trans_handlers: Dict[FileType, Type[BaseTransHandler]] = {
        FileType.CP: CPTransHandler,
        FileType.I18N: I18nTransHandler,
        FileType.MAIL: MailTransHandler,
        FileType.JA: JATransHandler,
        FileType.BL: BLTransHandler,
        FileType.STF: STFTransHandler,
        FileType.QF: QFTransHandler
    }

    @classmethod
    def get_trans_handler(cls, file_type: FileType) -> Type[BaseTransHandler]:
        handler_class = cls._trans_handlers.get(file_type)
        if not handler_class:
            raise ValueError(f"No handler found for file type: {file_type}")
        return handler_class
