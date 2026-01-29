import logging
import os
import re

import wjson

from app.common.constant import FileType, TargetAssetType, ActionType
from .BaseTransHandler import BaseTransHandler
from app.common.config import appConfig
from app.common.utils import file_util


def get_random_list(path):
    pattern = r"\{\{Random:([^\}]+)\}\}"
    match = re.search(pattern, path)

    if not match:
        return [path]

    placeholder = match.group(0)
    values_str = match.group(1)
    values = [s.strip() for s in values_str.split(",")]

    expanded_sentences = []
    for replacement in values:
        if replacement.lower() == "null":
            continue
        else:
            expanded_sentence = path.replace(placeholder, replacement)
        expanded_sentences.append(expanded_sentence)

    return expanded_sentences


class CPTransHandler(BaseTransHandler):
    def get_file_type(self) -> FileType:
        return FileType.CP

    def __init__(self, context):
        super().__init__(context)
        self.cp_path = None
        self.dynamicTokens = {}


    def replace_dynamic_token(self, text):
        return re.sub(r"\{\{([^}]+)}}", lambda match: self.dynamicTokens.get(match.group(1), match.group(0)), text)

    def convert_source_to_target_path(self, source_file_path):
        """
        将源语言文件路径转换为目标语言文件路径
        例如：i18n/en/Data/FarmAnimals.json -> i18n/zh_CN/Data/FarmAnimals.json
        
        Args:
            source_file_path: 源文件路径
            
        Returns:
            目标语言文件路径
        """
        # 标准化路径分隔符
        normalized_path = source_file_path.replace(os.sep, '/')
        
        # 尝试匹配 i18n/{language}/ 模式
        pattern = r'(.*?/i18n/)([^/]+)(/.+)$'
        match = re.match(pattern, normalized_path)
        
        if match:
            prefix = match.group(1)  # .../i18n/
            lang_folder = match.group(2)  # en 或 default
            suffix = match.group(3)  # /Data/xxx.json
            
            # 如果是源语言文件夹，替换为目标语言
            if lang_folder.lower() in ['en', 'default', appConfig.source_language.value.lower()]:
                target_path = f"{prefix}{appConfig.to_language.value}{suffix}"
                # 转回系统路径分隔符
                target_path = target_path.replace('/', os.sep)
                logging.info(f"Converting path from source to target language: {source_file_path} -> {target_path}")
                return target_path
        
        # 如果没有匹配到或不是源语言文件夹，返回原路径
        return source_file_path

    def replace_path_tokens(self, file_path, target=None, language_value=None):
        """
        替换文件路径中的占位符标记
        
        Args:
            file_path: 原始文件路径
            target: 目标字符串，用于替换{{Target}}和{{TargetWithoutPath}}
            language_value: 语言值，如果提供则替换{{Language}}/{{language}}
                          - 传入目标语言：appConfig.to_language.value
                          - 传入源语言：'default' 或 'en'
                          - 传入 None：不替换语言占位符
            
        Returns:
            替换后的文件路径
        """
        result = file_path
        
        # 替换 Target 相关的占位符
        if target is not None:
            targetWithoutPath = target[target.rfind("/") + 1:]
            result = result.replace("{{TargetWithoutPath}}", targetWithoutPath)
            result = result.replace("{{Target}}", target)
        
        # 替换 Language 占位符（大小写不敏感）
        if language_value is not None:
            if "{{Language}}" in result:
                result = result.replace("{{Language}}", language_value)
            elif "{{language}}" in result:
                result = result.replace("{{language}}", language_value)
        
        return result

    def resolve_source_file_path(self, file_path, target=None):
        """
        解析源文件路径，按优先级尝试: en -> default
        直接尝试打开文件，让 open() 自动抛异常（和老版本一样）
        
        Args:
            file_path: 原始文件路径（可能包含{{Language}}占位符）
            target: 目标字符串，用于替换{{Target}}和{{TargetWithoutPath}}
            
        Returns:
            实际存在的源文件完整路径
            
        Raises:
            FileNotFoundError: 如果所有尝试都失败（由 open() 自动抛出）
        """
        # 如果路径中没有Language占位符，直接返回路径（让 open() 去检查）
        if "{{Language}}" not in file_path and "{{language}}" not in file_path:
            return self.replace_path_tokens(file_path, target)
        
        # 按优先级尝试不同的语言值: en -> default
        for lang in ["en", "default"]:
            try_path = self.replace_path_tokens(file_path, target, lang)
            full_path = os.path.join(self.cp_path, try_path)
            logging.debug(f"Trying source file: {full_path}")
            
            # 直接尝试打开文件，如果失败会自动抛异常
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    # 文件存在且可以打开
                    logging.info(f"Found source file with language '{lang}': {try_path}")
                    return try_path
            except FileNotFoundError:
                logging.debug(f"File not found: {full_path}, will try next language option")
                continue
            except Exception as e:
                logging.debug(f"Failed to open {full_path}: {e}, will try next language option")
                continue
        
        # 如果都失败，尝试最后一次（会自动抛出 FileNotFoundError）
        final_path = self.replace_path_tokens(file_path, target, "en")
        full_path = os.path.join(self.cp_path, final_path)
        # 直接打开，让它抛异常
        with open(full_path, 'r', encoding='utf-8') as f:
            pass
        return final_path

    def load_source_file_with_fallback(self, file_path, target=None):
        """
        加载源文件内容，支持回退机制
        按优先级尝试: en -> default
        直接尝试打开并读取文件，让 open() 自动抛异常（和老版本一样）
        
        Args:
            file_path: 原始文件路径（可能包含{{Language}}占位符）
            target: 目标字符串，用于替换{{Target}}和{{TargetWithoutPath}}
            
        Returns:
            (source_path, entries): 实际读取的文件路径和解析后的内容
            
        Raises:
            FileNotFoundError: 如果文件不存在（由 open() 自动抛出）
            Exception: 如果文件读取失败
        """
        # 如果路径中没有Language占位符，直接读取文件
        if "{{Language}}" not in file_path and "{{language}}" not in file_path:
            source_path = self.replace_path_tokens(file_path, target)
            full_path = os.path.join(self.cp_path, source_path)
            # 直接读取，让 open() 自动抛异常
            with open(full_path, 'r', encoding='utf-8') as f:
                entries = wjson.load(f)
            return source_path, entries
        
        # 按优先级尝试不同的语言值: en -> default
        for lang in ["en", "default"]:
            try_path = self.replace_path_tokens(file_path, target, lang)
            full_path = os.path.join(self.cp_path, try_path)
            logging.debug(f"Trying to load: {full_path}")
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    entries = wjson.load(f)
                # 如果成功读取且内容不为空，返回结果
                if entries is not None:
                    logging.info(f"Successfully loaded source file with language '{lang}': {try_path}")
                    return try_path, entries
                else:
                    logging.debug(f"File content is None, trying next language option")
                    continue
            except FileNotFoundError:
                logging.debug(f"File not found: {full_path}, trying next language option")
                continue
            except Exception as e:
                logging.debug(f"Failed to load {full_path}: {e}, trying next language option")
                continue
        
        # 如果都失败，尝试最后一次（会自动抛出 FileNotFoundError）
        final_path = self.replace_path_tokens(file_path, target, "en")
        full_path = os.path.join(self.cp_path, final_path)
        # 直接读取，让它抛异常
        with open(full_path, 'r', encoding='utf-8') as f:
            entries = wjson.load(f)
        return final_path, entries

    def handle(self, file_path):
        print(f"CPTransHandler translations:{file_path}")

        i18n_folder = os.path.exists(file_util.get_i18n_folder(file_path))

        # 直接用 UTF-8 加载文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
        if content is None:
            return
        dynamicTokens = content.get("ConfigSchema")
        if dynamicTokens is not None:
            i18n_folder = file_util.get_i18n_folder(file_path)
            default_json_path = os.path.join(i18n_folder, "default.json")
            
            # 检查 i18n 文件夹第一层是否已经存在 json 文件
            # 如果不存在，说明采用新的子文件夹方式（如 i18n/zh/），不自动生成 default.json
            should_process_config = False
            if os.path.exists(i18n_folder):
                # 检查第一层是否有 .json 文件
                for item in os.listdir(i18n_folder):
                    item_path = os.path.join(i18n_folder, item)
                    if os.path.isfile(item_path) and item.endswith('.json'):
                        should_process_config = True
                        break
            
            # 只有当 i18n 第一层已经有 json 文件时，才处理 ConfigSchema
            if should_process_config:
                existing_translations = {}
                has_changes = False
                default_json_path_exist = os.path.exists(default_json_path)
                if default_json_path_exist:
                    with open(default_json_path, 'r', encoding='utf-8') as f:
                        existing_translations = wjson.load(f)

                existing_keys_lower = {k.lower(): k for k in existing_translations.keys()}

                for key, value in dynamicTokens.items():
                    default_value = value.get("Default")
                    if default_value is not None and isinstance(default_value, (int, float)):
                        continue

                    # Handle basic name
                    name_key = f"config.{key}.name"
                    if name_key.lower() not in existing_keys_lower:
                        self.dynamicTokens[name_key] = key
                        existing_translations[name_key] = key
                        has_changes = True

                    # Handle Description if exists
                    if "Description" in value:
                        desc_key = f"config.{key}.description"
                        if desc_key.lower() not in existing_keys_lower:
                            self.dynamicTokens[desc_key] = value["Description"]
                            existing_translations[desc_key] = value["Description"]
                            has_changes = True

                    # Handle Section if exists
                    if "Section" in value:
                        section_key = f"config.section.{key}.name"
                        if section_key.lower() not in existing_keys_lower:
                            self.dynamicTokens[section_key] = value["Section"]
                            existing_translations[section_key] = value["Section"]
                            has_changes = True

                    # Handle AllowValues if exists
                    if "AllowValues" in value:
                        values = [v.strip() for v in value["AllowValues"].split(",")]
                        for val in values:
                            if val.replace(".", "").isdigit() or val.lower() == 'true' or val.lower() == 'false':
                                continue

                            value_key = f"config.{key}.values.{val}"
                            if value_key.lower() not in existing_keys_lower:
                                self.dynamicTokens[value_key] = val
                                existing_translations[value_key] = val
                                has_changes = True

                if has_changes:
                    try:
                        with open(default_json_path, 'w', encoding='utf-8') as f:
                            wjson.dump(existing_translations, f)
                    except Exception as e:
                        logging.error(f"Error writing to default.json: {e}")

                    if not default_json_path_exist:
                        if FileType.I18N in self.context.files_by_type:
                            if default_json_path not in self.context.files_by_type[FileType.I18N]:
                                self.context.files_by_type[FileType.I18N].append(default_json_path)
                        else:
                            self.context.files_by_type[FileType.I18N] = [default_json_path]

        if not appConfig.i18n_extract_cp.value and i18n_folder:
            logging.info(f"exist i18n folder ignore extra CP ：{file_path}")
            return
        if os.path.basename(file_path) == "content.json":
            self.cp_path = os.path.dirname(file_path)
        relative_path = file_util.get_relative_path(file_path, self.context.mod_path)

        dynamicTokens = content.get("DynamicTokens")
        if dynamicTokens:
            for dynamicToken in dynamicTokens:
                name = dynamicToken.get("Name")
                value = dynamicToken.get("Value")
                when = dynamicToken.get("When")
                if value:
                    if name not in self.dynamicTokens:
                        self.dynamicTokens[name] = value
        changes = content.get("Changes")

        if changes is None or len(changes) == 0:
            return

        for i in range(len(changes)):
            change = changes[i]
            action = change.get("Action", "load")

            when = change.get("When")
            if when is not None and "When" in change and when.get("Language") is not None and when.get(
                    "Language") != appConfig.source_language.value:
                continue
            target = change.get("Target")
            base_key = get_base_key(relative_path, target, when)
            if action.lower() == "include":
                from_files = change.get("FromFile")
                for random_file in get_random_list(from_files):
                    # assets/Devan/Dialogue{{lang}}.json
                    random_file = self.replace_dynamic_token(random_file)
                    from_file_array = random_file.split(",")
                    for form_file in from_file_array:
                        form_file = form_file.strip()
                        if not form_file.endswith(".json"):
                            continue
                        if target is not None:
                            targets = target.split(",")
                            for target1 in targets:
                                if target1.strip() == "":
                                    continue
                                target1 = target1.strip()
                                # 使用统一的源文件路径解析（尝试 en -> default）
                                # 如果文件不存在会抛出异常，由 batch_handle 捕获并报错
                                source_path = self.resolve_source_file_path(form_file, target1)
                                self.batch_handle([os.path.join(self.cp_path, source_path)])
                        else:
                            print(self.cp_path)
                            print(form_file)
                            # 使用统一的源文件路径解析
                            # 如果文件不存在会抛出异常，由 batch_handle 捕获并报错
                            source_path = self.resolve_source_file_path(form_file)
                            self.batch_handle([os.path.join(self.cp_path, source_path)])
            elif action.lower() == "EditData".lower():
                target_field = change.get("TargetField")
                if target_field is not None:
                    continue
                target_type = TargetAssetType.get_target_asset_type(target)
                entries = get_field(change, "Entries")
                self.traverse_editdata_entries(target_type, entries, base_key)
                fields = change.get("Fields")
                self.traverse_editdata_fields(target_type, fields, base_key)
            elif action.lower() == "load":
                from_files = change.get("FromFile")
                if from_files is None or from_files.strip() == "":
                    continue
                for random_file in get_random_list(from_files):
                    random_file = self.replace_dynamic_token(random_file)
                    from_file_array = random_file.split(",")
                    for form_file in from_file_array:
                        form_file = form_file.strip()
                        if not form_file.endswith(".json"):
                            continue
                        targets = target.split(",")
                        for target1 in targets:
                            if target1.strip() == "":
                                continue
                            target1 = target1.strip()
                            # 使用统一的源文件加载方法（尝试 en -> default）
                            # 不仅检查文件存在性，还验证内容有效性
                            # 如果文件不存在或读取失败会抛出异常，由 batch_handle 捕获并报错
                            source_path, entries = self.load_source_file_with_fallback(form_file, target1)
                            target_type = TargetAssetType.get_target_asset_type(target1)
                            if self.traverse_editdata_entries(target_type, entries, base_key):
                                # 根据操作类型决定输出路径
                                if self.context.action_type == ActionType.GENERATE:
                                    # 生成翻译文件时：输出到目标语言路径
                                    if "{{Language}}" in form_file or "{{language}}" in form_file:
                                        # 使用模板路径，替换为目标语言
                                        output_path = self.replace_path_tokens(form_file, target1, appConfig.to_language.value)
                                    else:
                                        # 即使没有模板占位符，也尝试转换 i18n/en 或 i18n/default 路径
                                        output_path = self.convert_source_to_target_path(source_path)
                                else:
                                    # 提取阶段：保持源文件路径
                                    output_path = source_path
                                self.create_out_file(os.path.join(self.cp_path, output_path), entries)
            elif action.lower == "EditMap".lower():
                # {
                #     "Action": "EditMap",
                #     "Target": "Maps/Custom_TreasureCave",
                #     "MapTiles": [
                #         {
                #             "Position": {
                #                 "X": 10,
                #                 "Y": 7
                #             },
                #             "Layer": "Buildings",
                #             "SetProperties": {
                #                 "Success": "T Slingshot 34",
                #                 "Action": "SVE_Lock 1 74 money",
                #                 "Default": "{{i18n:TreasureCave.String.01}}",
                #                 "Failure": "{{i18n:TreasureCave.String.02}}",
                #             }
                #         }
                #     ]
                # }
                map_tiles = change.get("MapTiles")
                if map_tiles:
                    for map_tile in map_tiles:
                        set_properties = map_tile.get("SetProperties")
                        if set_properties:
                            default = set_properties.get("Default")
                            if default:
                                set_properties["Default"] = self.get_new_value("#".join([base_key, "Default"]), default,
                                                                               TargetAssetType.PlainText)
                            failure = set_properties.get("Failure")
                            if failure:
                                set_properties["Failure"] = self.get_new_value("#".join([base_key, "Failure"]), failure,
                                                                               TargetAssetType.PlainText)
        
        # 根据操作类型决定输出路径
        if self.context.action_type == ActionType.GENERATE:
            # 生成翻译文件时：将源语言路径转换为目标语言路径
            output_file_path = self.convert_source_to_target_path(file_path)
        else:
            # 提取阶段：保持源文件路径
            output_file_path = file_path
        
        self.create_out_file(output_file_path, content)

    def traverse_editdata_entries(self, targetType, entries, baseKey):
        flag = True
        if entries and len(entries) > 0:
            for key in entries.keys():
                dict_key = "#".join([baseKey, key])
                entry = entries[key]
                # entry is boolean
                if isinstance(entry, bool):
                    continue
                # print(entry)
                if (targetType == TargetAssetType.MoviesReactions
                        or targetType == TargetAssetType.MarriageMoviesReactions):
                    reactions = entry.get("Reactions")
                    npc_name = entry.get("NPCName")
                    for j in range(len(reactions)):
                        reaction = reactions[j]
                        id = reaction.get("ID")
                        special_responses = reaction.get("SpecialResponses")
                        if special_responses is None:
                            continue
                        for special_responses_key in special_responses.keys():
                            special_response = special_responses[special_responses_key]
                            if special_response is None:
                                continue
                            text = special_response.get("Text")
                            if text is not None and text.strip() != "":
                                special_response["Text"] = self.get_new_value(
                                    "#".join([dict_key, npc_name, id, special_responses_key]), text,
                                    TargetAssetType.PlainText)
                            script = special_response.get("Script")
                            if script is not None and script.strip() != "":
                                special_response["Script"] = self.get_new_value(
                                    "#".join([dict_key, npc_name, id, special_responses_key]), script,
                                    TargetAssetType.EventsLike)
                elif targetType == TargetAssetType.NPCMapLocations:
                    map_tooltip = entry.get("MapTooltip")
                    if map_tooltip is not None and map_tooltip.get("PrimaryText").strip() != "":
                        primary_text = map_tooltip.get("PrimaryText")
                        map_tooltip["PrimaryText"] = self.get_new_value(
                            "#".join([dict_key, "MapTooltip", "PrimaryText"]), primary_text, TargetAssetType.PlainText)
                elif targetType == TargetAssetType.WorldMap:
                    map_tooltip = entry.get("Tooltips")
                    if map_tooltip is not None and map_tooltip.get("Text").strip() != "":
                        text = map_tooltip.get("Text")
                        map_tooltip["Text"] = self.get_new_value(
                            "#".join([dict_key, "Tooltips", "Text"]), text, TargetAssetType.PlainText)
                    map_areas = entry.get("MapAreas")
                    if map_areas is not None:
                        for map_area in map_areas:
                            scroll_text = map_area.get("ScrollText")
                            map_area_id = map_area.get("Id") or map_area.get("ID")
                            if map_area_id and scroll_text is not None and scroll_text.strip() != "":
                                map_area["ScrollText"] = self.get_new_value(
                                    "#".join([dict_key, "MapAreas", map_area_id, "ScrollText"]), scroll_text,
                                    TargetAssetType.PlainText)
                elif targetType == TargetAssetType.DataSpecialOrders:
                    objectives = entry.get("Objectives")
                    for i in range(len(objectives)):
                        objective = objectives[i]
                        text = objective.get("Text")
                        if "[" not in text:
                            objective["Text"] = self.get_new_value("#".join([dict_key, "Objectives", str(i), "Text"]),
                                                                   text, TargetAssetType.PlainText)
                elif targetType == TargetAssetType.PassiveFestivals:
                    self.entry_field(dict_key, "DisplayName", entry)
                    self.entry_field(dict_key, "StartMessage", entry)
                elif (targetType == TargetAssetType.BigCraftables
                      or targetType == TargetAssetType.Objects
                      or targetType == TargetAssetType.Weapons
                      or targetType == TargetAssetType.Shirts
                      or targetType == TargetAssetType.Pants
                ):
                    self.entry_field(dict_key, "DisplayName", entry)
                    self.entry_field(dict_key, "Description", entry)
                elif (targetType == TargetAssetType.Locations
                      or targetType == TargetAssetType.FruitTrees):
                    self.entry_field(dict_key, "DisplayName", entry)
                elif targetType == TargetAssetType.Buildings:
                    self.entry_field(dict_key, "DisplayName", entry)
                    self.entry_field(dict_key, "Name", entry)
                elif targetType == TargetAssetType.FarmAnimal:
                    self.entry_field(dict_key, "DisplayName", entry)
                    self.entry_field(dict_key, "ShopDisplayName", entry)
                    self.entry_field(dict_key, "ShopDescription", entry)
                    self.entry_field(dict_key, "ShopMissingBuildingDescription", entry)
                    self.entry_field(dict_key, "BirthText", entry)
                elif targetType == TargetAssetType.Characters:
                    self.entry_field(dict_key, "DisplayName", entry)
                    friends_and_family = entry.get("FriendsAndFamily")
                    if friends_and_family:
                        for friendKey in friends_and_family.keys():
                            entry["FriendsAndFamily"][friendKey] = self.get_new_value(
                                "#".join([dict_key, "FriendsAndFamily", friendKey]),
                                friends_and_family[friendKey],
                                TargetAssetType.PlainText)
                elif targetType == TargetAssetType.JukeboxTracks:
                    self.entry_field(dict_key, "Name", entry)
                elif targetType == TargetAssetType.Shops:
                    owners = entry.get("Owners")
                    if owners is not None:
                        for owner in owners:
                            name = owner.get("Name")
                            closed_message = owner.get("ClosedMessage")
                            if closed_message is not None and closed_message.strip() != "":
                                owner["ClosedMessage"] = self.get_new_value(
                                    "#".join([dict_key, "Owners", name, "ClosedMessage"]), closed_message,
                                    TargetAssetType.PlainText)

                            dialogues = owner.get("Dialogues")
                            if dialogues is not None:
                                for dialogue in dialogues:
                                    dialogue_id = dialogue.get("Id")
                                    dialogue_text = dialogue.get("Dialogue")
                                    if dialogue_text is not None:
                                        dialogue["Dialogue"] = self.get_new_value(
                                            "#".join([dict_key, "Owners", name, "Dialogues", dialogue_id]),
                                            dialogue_text,
                                            TargetAssetType.PlainText)
                elif targetType == TargetAssetType.CheatsMenu:
                    self.entry_field(dict_key, "DisplayName", entry)
                elif targetType == TargetAssetType.Minecarts:
                    destinations = entry.get("Destinations")
                    if destinations is not None:
                        for destination in destinations:
                            destination_id = destination.get("Id") or destination.get("ID")
                            self.entry_field("#".join([dict_key, "Destinations", destination_id]), "DisplayName",
                                             destination)
                elif targetType == TargetAssetType.ClothingInformation and not isinstance(entry, str):
                    self.entry_field(dict_key, "DisplayName", entry)
                    self.entry_field(dict_key, "Description", entry)
                elif targetType == TargetAssetType.Bundles:
                    self.entry_field(dict_key, "BundleName", entry)
                    self.entry_field(dict_key, "BundleDescription", entry)
                elif targetType != TargetAssetType.Unknown and isinstance(entry, str):
                    entries[key] = self.get_new_value(dict_key, entry, targetType)
                else:
                    flag = False
        return flag

    def entry_field(self, dict_key, field_name, entry):
        field_name_lower = field_name.lower()
        for key in entry.keys():
            if key.lower() == field_name_lower:
                field_value = entry.get(key)
                if field_value and field_value.strip():
                    entry[key] = self.get_new_value("#".join([dict_key, key]),
                                                    field_value,
                                                    TargetAssetType.PlainText)
                break

    def traverse_editdata_fields(self, target_type, fields, base_key):
        flag = False
        if fields is not None and len(fields) > 0:
            for key in fields.keys():
                dictKey = "#".join([base_key, key])
                field = fields[key]
                if target_type == TargetAssetType.ObjectInformation:
                    str4 = field.get("4")
                    if str4 and str4.strip() != "":
                        field["4"] = self.get_new_value("#".join([dictKey, "4"]), str4, TargetAssetType.PlainText)
                        flag = True
                    str5 = field.get("5")
                    if str5 and str5.strip() != "":
                        field["5"] = self.get_new_value("#".join([dictKey, "5"]), str5, TargetAssetType.PlainText)
                        flag = True
                elif target_type in [TargetAssetType.SecretNotes, TargetAssetType.Festivals, TargetAssetType.PlainText]:
                    str0 = field.get("0")
                    if str0 and str0.strip() != "":
                        field["0"] = self.get_new_value("#".join([dictKey, "0"]), str0, TargetAssetType.PlainText)
                        flag = True
        return flag


def get_base_key(relative_path, target, when):
    when_string = ""
    if when is not None:
        for key, value in when.items():
            when_string += f"[{key}:{value}]"

    parts = [relative_path, target if target is not None else "", when_string]
    return "#".join(parts)


def get_field(entry, field_name):
    field_name_lower = field_name.lower()
    for key in entry.keys():
        if key.lower() == field_name_lower:
            field_value = entry.get(key)
            return field_value
    return None
