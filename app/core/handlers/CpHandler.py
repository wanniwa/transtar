import logging
import os
import re

import wjson

from app.common.constant import FileType, TargetAssetType
from .BaseTransHandler import BaseTransHandler
from app.common.config import uiConfig
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

    def handle(self, file_path):
        print(f"CPTransHandler translations:{file_path}")

        i18n_folder = os.path.exists(file_util.get_i18n_folder(file_path))

        with open(file_path, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
        if content is None:
            return
        dynamicTokens = content.get("ConfigSchema")
        if dynamicTokens is not None:
            i18n_folder = file_util.get_i18n_folder(file_path)
            default_json_path = os.path.join(i18n_folder, "default.json")
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
                os.makedirs(i18n_folder, exist_ok=True)

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

        if not uiConfig.i18n_extract_cp.value and i18n_folder:
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
                    "Language") != uiConfig.source_language.value:
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
                                targetWithoutPath = target1[target1.rfind("/") + 1:]
                                form_file1 = form_file.replace("{{TargetWithoutPath}}", targetWithoutPath)
                                form_file1 = form_file1.replace("{{Target}}", target1)
                                self.batch_handle([os.path.join(self.cp_path, form_file1)])
                        else:
                            print(self.cp_path)
                            print(form_file)
                            self.batch_handle([os.path.join(self.cp_path, form_file)])
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
                            targetWithoutPath = target1[target1.rfind("/") + 1:]
                            form_file1 = form_file.replace("{{TargetWithoutPath}}", targetWithoutPath)
                            form_file1 = form_file1.replace("{{Target}}", target1)
                            with open(os.path.join(self.cp_path, form_file1.replace("{{Language}}", "default")), 'r',
                                      encoding='utf-8') as f:
                                entries = wjson.load(f)
                            if entries is None:
                                with open(os.path.join(self.cp_path, form_file1.replace("{{Language}}", "en")), 'r',
                                          encoding='utf-8') as f:
                                    entries = wjson.load(f)
                            target_type = TargetAssetType.get_target_asset_type(target1)
                            if self.traverse_editdata_entries(target_type, entries, base_key):
                                if "{{Language}}" in form_file1:
                                    form_file1 = form_file1.replace("{{Language}}", uiConfig.to_language.value)
                                self.create_out_file(os.path.join(self.cp_path, form_file1), entries)
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
        self.create_out_file(file_path, content)

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
