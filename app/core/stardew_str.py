import re

from app.common.constant import TargetAssetType, FileType
from app.common.utils import trans_util
from app.common.utils.trans_util import random_pattern
from app.core.handlers.trans_context import TransContext

event_pattern = r'(?i)(speak\s+[^ ]+|splitSpeak\s+[^ ]+|textAboveHead\s+[^ ]+|end dialogue\s+[^ ]+|end dialogueWarpOut\s+[^ ]+|message|quickQuestion|question\s+[^ ]+)\s+\"?(.*?)\"?\s*(?=\(break\)|\\|/|$)'


class StardewStr:
    def __init__(self, key, raw, target_type: TargetAssetType, context: TransContext, dict_cache):
        self.dict = {}
        self.key = key
        self.raw = raw
        self.target_type = target_type
        self.context = context
        self.tran_after = raw
        self.need_translate = True
        self.index = 0
        self.dict_cache = dict_cache

    def deal_str(self):
        if self.target_type == TargetAssetType.PlainText:
            if self.context.file_type == FileType.CP and '/' in self.raw and '$q' not in self.raw:
                self.events_like()
            else:
                self.plain_text()
        elif self.target_type == TargetAssetType.EventsLike:
            self.events_like()
        elif self.target_type == TargetAssetType.Festivals:
            if "set-up" in self.key.lower() or "conditions" in self.key.lower() or self.key == "shop" or "name" in self.key.lower():
                self.no_need_translate()
            elif '/' in self.raw:
                self.events_like()
            else:
                self.plain_text()
        elif self.target_type == TargetAssetType.NPCDispositions:
            self.npc_dispositions()
        elif self.target_type == TargetAssetType.NPCGiftTastes:
            self.npc_gift_tastes()
        elif self.target_type == TargetAssetType.Mail:
            self.mail()
        elif self.target_type == TargetAssetType.ObjectInformation:
            self.object_information()
        elif self.target_type == TargetAssetType.Quests:
            self.quests()
        elif self.target_type == TargetAssetType.BigCraftablesInformation:
            self.big_craftables_information()
        elif self.target_type == TargetAssetType.CookingRecipes:
            self.cooking_recipes()
        elif self.target_type == TargetAssetType.Hats:
            self.hats()
        elif self.target_type == TargetAssetType.Boots:
            self.boots()
        elif self.target_type == TargetAssetType.ClothingInformation:
            self.clothing_information()
        elif self.target_type == TargetAssetType.Furniture:
            self.furniture()
        return self.tran_after

    def plain_text(self):
        self.tran_after = self.deal_random_token(self.raw)

    def events_like(self):
        def replace_match(match):
            prefix = match.group(1)
            matched_text = match.group(2)

            translated_text = self.deal_token(matched_text)

            if translated_text == matched_text:
                return match.group(0)
            return match.group(0).replace(matched_text, translated_text)

        if self.check_speak_text():
            self.tran_after = re.sub(event_pattern, replace_match, self.raw)
        else:
            self.no_need_translate()

    def check_speak_text(self):
        found_match = False
        dialogs = re.findall(event_pattern, self.raw)
        if dialogs:
            found_match = True
        return found_match

    def no_need_translate(self):
        self.need_translate = False

    def npc_dispositions(self):
        str_li = self.raw.split("/")
        index = 11
        if len(str_li) > index:
            npc_name = str_li[index]
            if "·" in npc_name:
                self.no_need_translate()
                return
            else:
                str_li[index] = self.deal_token(npc_name)
        self.tran_after = "/".join(str_li)

    def npc_gift_tastes(self):
        str_li = self.raw.split("/")
        # Iterate through the string list, where the segments with even indices need to be translated
        for index in range(len(str_li)):
            if index % 2 == 0:
                str_li[index] = self.deal_token(str_li[index])
        self.tran_after = "/".join(str_li)

    def mail(self):
        str_li = re.split(r'\s*\[#]\s*', self.raw)
        if len(str_li) <= 2:
            pattern_compile = re.compile(r'\s*%item.*%%')
            matcher = pattern_compile.search(str_li[0])
            if matcher:
                self.tran_after = self.deal_token(str_li[0][:matcher.start()]) + matcher.group() + str_li[0][
                                                                                                   matcher.end():]
            else:
                self.tran_after = self.deal_token(str_li[0])
            if len(str_li) == 2:
                self.tran_after += "[#]" + self.deal_token(str_li[1])
        else:
            print("email format error: " + self.raw)

    def object_information(self):
        split = self.raw.split("/")
        split[4] = self.deal_token(split[4])
        split[5] = self.deal_token(split[5])
        self.tran_after = "/".join(split)

    def quests(self):
        split = self.raw.split("/")
        split[1] = self.deal_token(split[1])
        split[2] = self.deal_token(split[2])
        split[3] = self.deal_token(split[3])
        if len(split) >= 10:
            if "{{spacechase0.JsonAssets/" in self.raw:
                split[10] = self.deal_token(split[10])
            else:
                split[9] = self.deal_token(split[9])
        self.tran_after = "/".join(split)

    def big_craftables_information(self):
        split = self.raw.split("/")
        split[4] = self.deal_token(split[4])
        split[8] = self.deal_token(split[8])
        self.tran_after = "/".join(split)

    def hats(self):
        split = self.raw.split("/")
        split[1] = self.deal_token(split[1])
        split[5] = self.deal_token(split[5])
        self.tran_after = "/".join(split)

    def deal_random_token(self, value: str) -> str:
        if "{{Random:" in value:
            random_data_list = []
            for match in random_pattern.finditer(value):
                random_data_list.append({
                    "randomData": match.group(1),
                    "separator": match.group(2)
                })

            for random_data in random_data_list:
                split = random_data["randomData"].split(random_data["separator"])
                for i in range(len(split)):
                    split[i] = self.deal_token(split[i])
                value = value.replace(random_data["randomData"], " ".join(split))
        else:
            value = self.deal_token(value)
        return value

    def deal_token(self, token):
        if self.context is None:
            return token
        key = self.key if self.index == 0 else self.key + "|" + str(self.index)
        self.index += 1

        if token.strip() == "":
            return token
        if token in self.context.trans_cache:
            new_token = self.context.trans_cache[token]
            return new_token

        if token in self.dict_cache:
            star_dict = self.dict_cache[token]
            new_token = star_dict["translation"]
        else:
            # 关键翻译位
            new_token = token

        self.context.trans_cache[token] = new_token
        # need dict
        if self.context.dict_flag:
            self.context.star_dicts.append(create_star_dict(key, token, new_token, len(self.context.star_dicts) + 1))
            return token
        else:
            trait = trans_util.trait(token)
            new_trait = trans_util.trait(new_token)
            if trait != new_trait:
                self.context.error_star_dicts.append(
                    trans_util.create_error_star_dict(key, token, new_token, trait, new_trait))
            return new_token

    def cooking_recipes(self):
        parts = self.raw.split('/')
        if len(parts) >= 5:
            parts[4] = self.deal_token(parts[4])
            self.tran_after = "/".join(parts)
        else:
            self.no_need_translate()

    def crafting_recipes(self):
        parts = self.raw.split('/')
        if len(parts) >= 6:
            parts[5] = self.deal_token(parts[5])
            self.tran_after = "/".join(parts)
        else:
            self.no_need_translate()

    def boots(self):
        parts = self.raw.split('/')
        parts[1] = self.deal_token(parts[1])
        if len(parts) >= 7:
            parts[6] = self.deal_token(parts[6])
        self.tran_after = "/".join(parts)

    def clothing_information(self):
        parts = self.raw.split('/')
        parts[1] = self.deal_token(parts[1])
        parts[2] = self.deal_token(parts[2])
        self.tran_after = "/".join(parts)

    def furniture(self):
        parts = self.raw.split('/')
        if len(parts) >= 8:
            parts[7] = self.deal_token(parts[7])
            self.tran_after = "/".join(parts)
        else:
            self.no_need_translate()


def create_star_dict(key, original, translation, num):
    return {
        "num": num,
        "key": key,
        "original": original,
        "translation": translation,
        "stage": 0,
    }
