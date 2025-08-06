from typing import Dict, List

from app.common.constant import FileType, ActionType


class TransContext:
    def __init__(self, mod_path: str, dict_flag: bool, trans_flag: bool, action_type: ActionType, file_type: FileType,
                 files_by_type: Dict[FileType, List[str]]):
        self.mod_path = mod_path
        self.dict_flag = dict_flag
        self.trans_flag = trans_flag
        self.action_type = action_type
        self.file_type = file_type
        self.files_by_type = files_by_type

        self.key_value_map = {}
        self.star_dicts = []
        self.error_star_dicts = []
        self.trans_cache = {}

    def get_duplicate_new_key(self, key):
        num = self.key_value_map.get(key, 0)
        num += 1
        self.key_value_map[key] = num
        key = key + "#" + str(num)
        return key
