import wjson
import os

from app.common.constant import FileType, TargetAssetType
from .base_handler import BaseTransHandler
from ...common.utils import file_util
from ...common.config import cfg


class I18nTransHandler(BaseTransHandler):
    def get_file_type(self) -> FileType:
        return FileType.I18N

    def handle(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = wjson.load(f)

        relative_path = file_util.get_relative_path(file_path, self.context.mod_path)
        for key in content.keys():
            value = content[key]
            paratranz_key = relative_path + "#" + key
            content[key] = self.get_new_value(paratranz_key, value, TargetAssetType.PlainText)

        translate_file_path = os.path.join(os.path.dirname(file_path), f"{cfg.to_language.value}.json")
        self.create_out_file(translate_file_path, content)
