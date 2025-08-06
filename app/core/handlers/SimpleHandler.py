import os

import wjson

from app.common.constant import FileType, TargetAssetType
from app.common.utils.file_util import get_i18n_folder, get_relative_path
from app.core.handlers.base_handler import BaseTransHandler
from app.common.config import uiConfig


class MailTransHandler(BaseTransHandler):
    def handle(self, file_path):
        if os.path.exists(get_i18n_folder(file_path)):
            return

        relative_path = get_relative_path(file_path, self.context.mod_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            contentStr = f.read()
            if "Changes" in contentStr:
                return
            content = wjson.loads(contentStr)

        for i in range(len(content)):
            mail_content = content[i]
            id_key = mail_content.get("Id")

            title_key = "Title"
            title_path = f"{relative_path}#{id_key}#{title_key}"
            if mail_content.get(title_key):
                mail_content[title_key] = self.get_new_value(title_path, mail_content.get(title_key),
                                                             TargetAssetType.PlainText)

            text_key = "Text"
            raw = mail_content.get(text_key)
            text_path = f"{relative_path}#{id_key}#{text_key}"
            if raw is not None:
                mail_content[text_key] = self.get_new_value(text_path, raw, TargetAssetType.Mail)

        self.create_out_file(file_path, content)

        print(f"MailTransHandler translations {file_path}")

    def get_file_type(self) -> FileType:
        return FileType.MAIL


class BLTransHandler(BaseTransHandler):
    def handle(self, file_path):
        relative_path = get_relative_path(file_path, self.context.mod_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
        if content is None:
            return
        display_name = content["displayname"]
        content["displayname"] = self.get_new_value(relative_path + "#" + "displayname", display_name,
                                                    TargetAssetType.PlainText)
        print(f"BLTransHandler translations,{file_path}")
        self.create_out_file(file_path, content)

    def get_file_type(self) -> FileType:
        return FileType.BL


class STFTransHandler(BaseTransHandler):
    def handle(self, file_path):
        relative_path = get_relative_path(file_path, self.context.mod_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
        if content is None:
            return
        shops = content.get("Shops")
        if shops is None:
            return
        for jsonObject in shops:
            shop_name = jsonObject.get("ShopName")
            quote = jsonObject.get("Quote")
            if quote:
                localized_quote = jsonObject.get("LocalizedQuote")
                if localized_quote is None:
                    localized_quote = {}
                    jsonObject["LocalizedQuote"] = localized_quote
                quote_key = f"{relative_path}#{shop_name}#Quote"
                localized_quote[uiConfig.to_language.value] = self.get_new_value(quote_key, quote,
                                                                                 TargetAssetType.PlainText)

            closed_message = jsonObject.get("ClosedMessage")
            if closed_message:
                localized_closed_message = jsonObject.get("LocalizedClosedMessage")
                if localized_closed_message is None:
                    localized_closed_message = {}
                    jsonObject["LocalizedClosedMessage"] = localized_closed_message
                closed_message_key = f"{relative_path}#{shop_name}#ClosedMessage"
                localized_closed_message[uiConfig.to_language.value] = self.get_new_value(closed_message_key,
                                                                                          closed_message,
                                                                                          TargetAssetType.PlainText)

        print(f"STFTransHandler translations {file_path}")

        self.create_out_file(file_path, content)

    def get_file_type(self) -> FileType:
        return FileType.STF


class QFTransHandler(BaseTransHandler):
    def handle(self, file_path):
        relative_path = get_relative_path(file_path, self.context.mod_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
        if content is None:
            return
        quests = content.get("Quests")
        if quests is None:
            return
        for jsonObject in quests:
            name_key = "Name"
            name = jsonObject.get(name_key)
            title_key = "Title"
            title = jsonObject.get(title_key)
            description_key = "Description"
            description = jsonObject.get(description_key)
            objective_key = "Objective"
            objective = jsonObject.get(objective_key)
            reaction_text_key = "ReactionText"
            reaction_text = jsonObject.get(reaction_text_key)

            base_key = f"{relative_path}#{name}#"
            jsonObject[title_key] = self.get_new_value(f"{base_key}{title_key}", title, TargetAssetType.PlainText)
            jsonObject[description_key] = self.get_new_value(f"{base_key}{description_key}", description,
                                                             TargetAssetType.PlainText)
            if objective:
                jsonObject[objective_key] = self.get_new_value(f"{base_key}{objective_key}", objective,
                                                               TargetAssetType.PlainText)
            if reaction_text:
                jsonObject[reaction_text_key] = self.get_new_value(f"{base_key}{reaction_text_key}", reaction_text,
                                                                   TargetAssetType.PlainText)

        self.create_out_file(file_path, content)

        print(f"QFTransHandler translations,{file_path}")

    def get_file_type(self) -> FileType:
        return FileType.QF


class JATransHandler(BaseTransHandler):
    def handle(self, file_path):
        file_name = os.path.basename(file_path)
        if file_name == "recipe.json":
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
        if content is None:
            return
        if "TranslationKey" in content:
            return
        if file_name.lower() == "crop.json":
            name_key = "SeedName"
            description_key = "SeedDescription"
            name_localization_key = "SeedNameLocalization"
            description_localization_key = "SeedDescriptionLocalization"
        elif file_name.lower() == "tree.json":
            name_key = "SaplingName"
            description_key = "SaplingDescription"
            name_localization_key = "SaplingNameLocalization"
            description_localization_key = "SaplingDescriptionLocalization"
        else:
            name_key = "Name"
            description_key = "Description"
            name_localization_key = "NameLocalization"
            description_localization_key = "DescriptionLocalization"
        name = content.get(name_key, "")
        if not name:
            raise Exception("no Name in file：" + file_path)
        description = content.get(description_key, "")
        name_localization = content.get(name_localization_key, {})
        if not name_localization:
            name_localization = {}
            content[name_localization_key] = name_localization
        description_localization = content.get(description_localization_key, {})
        if not description_localization:
            description_localization = {}
            content[description_localization_key] = description_localization

        relative_path = get_relative_path(file_path, self.context.mod_path)
        self.do_ja_localization(name_localization, name_key, name, relative_path)
        self.do_ja_localization(description_localization, description_key, description, relative_path)
        self.create_out_file(file_path, content)

    def do_ja_localization(self, localization, key, value, relative_path):
        trans_key = relative_path + "#" + key
        if self.context.trans_flag:
            localization[uiConfig.to_language.value] = self.get_new_value(trans_key, value, TargetAssetType.PlainText)
        elif self.context.dict_flag:
            self.get_new_value(trans_key, value, TargetAssetType.PlainText)

    def get_file_type(self) -> FileType:
        return FileType.JA


class UnknownTransHandler(BaseTransHandler):
    def get_file_type(self):
        return FileType.UNKNOWN

    def handle(self, file_path):
        print("UnknownTransHandler translations")
