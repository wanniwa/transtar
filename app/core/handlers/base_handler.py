from abc import ABC, abstractmethod
import os
import json
from app.common.constant import FileType, TargetAssetType
from app.common.utils.notify_util import notify_error
from app.common.utils.file_util import get_dict_path, get_error_dict_path, get_out_path
from app.core.handlers.trans_context import TransContext
from app.core.stardew_str import StardewStr
from app.common.config import cfg


class BaseTransHandler(ABC):
    def __init__(self, context: TransContext):
        self.context = context
        self.dict_cache = {}
        self.dict_path = get_dict_path(context.mod_path)
        self.error_dict_path = get_error_dict_path(context.mod_path)
        dict_file_path = self.dict_path + "/" + self.get_file_type().file_name
        if os.path.exists(dict_file_path):
            with open(dict_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data:
                    if 'original' in entry and 'translation' in entry:
                        if entry['translation'] != '' and entry['translation'] != entry['original']:
                            entry['original'] = entry['original'].replace("\\n", "\n")
                            entry['translation'] = entry['translation'].replace("\\n", "\n")
                            self.dict_cache[entry['original']] = entry

    @abstractmethod
    def get_file_type(self) -> FileType:
        """Return the FileType enum value for this handler"""
        pass

    @abstractmethod
    def handle(self, file_path):
        """Handle single file translation"""
        pass

    def batch_handle(self, files):
        for file in files:
            try:
                self.handle(file)
            except Exception as e:
                notify_error(e, file)

    def create_out_file(self, file_path, out_obj):
        if self.context.action_type != 2:
            return
        out_file_path = get_out_path(self.context.mod_path) + "/" + os.path.relpath(file_path,
                                                                                    self.context.mod_path)

        out_json = json.dumps(out_obj, indent=4, ensure_ascii=False)

        # 检查文件是否存在
        if not os.path.exists(out_file_path):
            # 创建文件夹
            os.makedirs(os.path.dirname(out_file_path), exist_ok=True)
        with open(out_file_path, 'w', encoding='utf-8') as file:
            file.write(out_json)

    def create_dict_file(self):
        if not os.path.exists(self.dict_path):
            os.makedirs(self.dict_path)
        if len(self.context.star_dicts) > 0:
            print("create dict【" + self.get_file_type().file_name + "】 num:" + str(len(self.context.star_dicts)))
            dict_file_path = self.dict_path + "/" + self.get_file_type().file_name
            dict_json = json.dumps(self.context.star_dicts, indent=4, ensure_ascii=False)

            with open(dict_file_path, 'w', encoding='utf-8') as file:
                file.write(dict_json)

    def create_error_dict_file(self):
        if len(self.context.error_star_dicts) > 0:
            if not os.path.exists(self.error_dict_path):
                os.makedirs(self.error_dict_path)
            print("find error dict【" + self.get_file_type().file_name + "】 num:" + str(
                len(self.context.error_star_dicts)))
            dict_file_path = self.error_dict_path + "/" + self.get_file_type().file_name
            dict_json = json.dumps(self.context.error_star_dicts, indent=4, ensure_ascii=False)

            with open(dict_file_path, 'w', encoding='utf-8') as file:
                file.write(dict_json)
            return True
        else:
            return False

    def get_trans_after_path(self):
        return self.context.mod_path + " " + cfg.to_language.value

    def get_new_value(self, key, raw, target_type: TargetAssetType):
        # max length of key is 230,can change,not suggest
        key = key[:230]
        if (not raw
                or "i18n" in raw.lower()
                and self.get_file_type() != FileType.I18N
                or raw == "null"
                or "LocalizedText Strings" in raw):
            return raw

        # Duplicate key
        if key in self.context.key_value_map:
            key = self.context.get_duplicate_new_key(key)

        stardew_str = StardewStr(key, raw, target_type, self.context, self.dict_cache)

        new_value = stardew_str.deal_str()
        need_translate = stardew_str.need_translate

        if need_translate:
            self.context.key_value_map[key] = 0

        if not self.context.trans_flag:
            return raw
        return new_value
