import wjson
import os

from app.common.constant import FileType, TargetAssetType
from .BaseTransHandler import BaseTransHandler
from ...common.utils import file_util
from ...common.config import appConfig


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

        # Determine the correct output file path based on i18n structure
        file_folder_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        parent_folder_name = os.path.basename(file_folder_path)
        
        # Scenario 1: File name directly indicates language (i18n/zh.json -> i18n/target_lang.json)
        if parent_folder_name.lower() == "i18n":
            translate_file_path = os.path.join(file_folder_path, f"{appConfig.to_language.value}.json")
        else:
            # Scenario 2: Language indicated by folder name (i18n/zh/lucy.json -> i18n/target_lang/lucy.json)
            grandparent_folder_path = os.path.dirname(file_folder_path)
            grandparent_folder_name = os.path.basename(grandparent_folder_path)
            
            if grandparent_folder_name.lower() == "i18n":
                # Create target language folder under i18n
                target_lang_folder = os.path.join(grandparent_folder_path, appConfig.to_language.value)
                translate_file_path = os.path.join(target_lang_folder, file_name)
            else:
                # Fallback to original behavior if structure doesn't match expected patterns
                translate_file_path = os.path.join(file_folder_path, f"{appConfig.to_language.value}.json")
        
        self.create_out_file(translate_file_path, content)
