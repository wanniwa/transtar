import wjson
import os
import platform
import re
import subprocess
import time

import deepl
from PySide6.QtWidgets import QMessageBox
from openai import OpenAI
from translatepy.translators.google import GoogleTranslateV2

from app.common.constant import LANGUAGE_KEY_NAME
from app.common.config import appConfig

random_pattern = re.compile(r"\{\{Random:(.*?)\|inputSeparator=(.*?)}}")


def trait(s):
    # Define the regular expression pattern
    pattern = r"\$\{\{[^{}]*?\}} #|\$\{\{[^{}]*?\}}#|\{\{[^{}]*?\}}|\^|\s*%item.*%%|#|%fork|%noturn|%adj|%noun|%place|%spouse|%name|%firstnameletter|%time|%band|%book|%rival|%pet|%farm|%favorite|%kid1|%kid2|\$q.*?#|\$r.*?#|\$[A-Za-z0-9]+|\$\{[^{}]*\}"

    # Find all matches of the pattern in the input string
    matches = re.findall(pattern, s)

    # Join the matches into a single string separated by "||"
    return '||'.join(matches)


# 此函数已废弃，翻译逻辑现在在 Action.translate() 中使用平台配置
def translate(value):
    raise NotImplementedError("此函数已废弃，请使用 Action.translate() 中的平台配置")


def batch_translate(dict_values, platform=None):
    values = list(dict_values)
    print(f'translate_put: {values}')
    api_format = None
    if platform:
        api_format = (platform.get("api_format") or "").lower()
    else:
        api_format = (appConfig.trans_model.value or "").lower()

    if api_format in ("google", "deepl"):
        result = []
        for value in values:
            result.append(modTrans(value, platform))
        return result

    # 其它模型不在此处处理（Action 内会走 LLMRequester）
    raise ValueError("batch_translate 仅用于 google/deepl 路径")


cache = {}


def google_translate(text, source_language, target_language):
    translate = GoogleTranslateV2().translate(text, target_language, source_language)
    return translate.result


def deepl_translate(text, source_language, target_language, platform=None):
    api_key = ""
    if platform:
        api_key = platform.get("api_key", "") or ""
    if not api_key:
        raise ValueError("DeepL API key not configured in platform settings")
    translator = deepl.Translator(api_key)
    result = translator.translate_text(text, source_lang=source_language, target_lang=target_language)
    return result.text


def transText(text, source_language, target_language, platform=None):
    if not text:
        return text
    if text.strip() == '':
        return text
    if source_language == 'en' and no_exist_text(text):
        return text
    if text in cache and cache[text]:
        return cache[text]

    api_format = None
    if platform:
        api_format = (platform.get("api_format") or "").lower()
    else:
        # 默认使用 google
        api_format = "google"

    if api_format == "deepl":
        result = deepl_translate(text, source_language, target_language, platform)
    else:
        result = google_translate(text, source_language, target_language)

    cache[text] = result
    return result


def modTrans(value, platform=None):
    print(f'translate_put: {value}')
    source_language = appConfig.source_language.value
    to_language = appConfig.to_language.value
    if value == "":
        return value

    if source_language == 'en' and no_exist_text(value):
        return value

    if value in cache:
        return cache[value]
    new_value = value

    api_format = None
    if platform:
        api_format = (platform.get("api_format") or "").lower()
    else:
        # 默认使用 google
        api_format = "google"

    if api_format not in ("google", "deepl"):
        # 其它模型不在此处处理
        return value

    if to_language == "zh":
        if source_language == "en":
            new_value = new_value.replace("@", "WangNing")
            new_value = new_value.replace("%adj", "变态")
            new_value = new_value.replace("%noun", "电脑管家")
            new_value = new_value.replace("%place", "紫荆山")
            new_value = new_value.replace("%spouse", "夏梦琪")
            new_value = new_value.replace("%name", "仲济川")
            new_value = new_value.replace("%firstnameletter", "王女士")
            new_value = new_value.replace("%time", "five o'clock")
            new_value = new_value.replace("%band", "超级乐队")
            new_value = new_value.replace("%book", "童话王国")
            new_value = new_value.replace("%rival", "秦淮河")
            new_value = new_value.replace("%pet", "旺财")
            new_value = new_value.replace("%farm", "QQ")
            new_value = new_value.replace("%kid1", "王帅哥")
            new_value = new_value.replace("%kid2", "李帅哥")
            new_value = new_value.replace("%year", "2029")
            new_value = new_value.replace("Nexus", "链接")

    pattern = r"#|\$q.*?#|\$r.*?#|\s*%item.*%%|\$.\{1}|\^+|\$\{\{[^{}]*?}} #|\$\{\{[^{}]*?}}#|\{\{.*}}|\n|%fork|\*|\{.*}|%revealtaste.*?(?=#)|%|\||\s*-+"
    split = re.split(pattern, new_value)
    if len(split) == 0:
        return value
    strings = re.findall(pattern, new_value)
    builder = ""
    for i in range(len(split)):
        all = split[i]
        if all == '':
            if i < len(strings):
                builder += strings[i]
            continue

        index = all.find("$")
        if index != -1:
            prev = all[:index]
            next = all[index:]
            # for prev data handling
            trans = transText(prev, source_language, to_language, platform)
            # for next data handling
            trans += next
        else:
            trans = transText(all, source_language, to_language, platform)

        if len(split) >= len(strings):
            builder += trans
            if i < len(strings):
                builder += strings[i]
        else:
            if i < len(strings):
                builder += strings[i]
            builder += trans
    new_value = builder
    if to_language == "zh":
        if source_language == "en":
            new_value = new_value.replace("王宁", "@")
            new_value = new_value.replace("WangNing", "@")
            new_value = new_value.replace("Wang Ning", "@")
            new_value = new_value.replace("变态", "%adj")
            new_value = new_value.replace("电脑管家", "%noun")
            new_value = new_value.replace("紫荆山", "%place")
            new_value = new_value.replace("夏梦琪", "%spouse")
            new_value = new_value.replace("仲济川", "%name")
            new_value = new_value.replace("王女士", "%firstnameletter")
            new_value = new_value.replace("5点", "%time")
            new_value = new_value.replace("超级乐队", "%band")
            new_value = new_value.replace("童话王国", "%book")
            new_value = new_value.replace("秦淮河", "%rival")
            new_value = new_value.replace("旺财", "%pet")
            new_value = new_value.replace("QQ", "%farm")
            new_value = new_value.replace("王帅哥", "%kid1")
            new_value = new_value.replace("李帅哥", "%kid2")
            new_value = new_value.replace("Pelican", "鹈鹕")
            new_value = new_value.replace("。。。", "……")
            new_value = new_value.replace("。。", "..")
            new_value = new_value.replace("UH", "嗯")
            new_value = new_value.replace("六羟甲基三聚氰胺六甲醚", "嗯")
            new_value = new_value.replace("隐马尔可夫模型", "嗯")
            new_value = new_value.replace("2029", "%year")
    print(f'translate_out: {new_value}')
    return new_value


def no_exist_text(text) -> bool:
    pattern = r'[a-zA-Z]'
    trait_regexp = r"\{\{[^{}]*?}}|\^|\|\[#]|#|@|%fork|%noturn|%adj|%noun|%place|%spouse|%name|%firstnameletter|%time|%band|%book|%rival|%pet|%farm|%favorite|%kid1|%kid2|\$(e|b|q\s*-?\d*\s*-?\d*|r\s*-?\d*\s*-?\d*\s*\w*|\d*)"
    result_string = re.sub(trait_regexp, "", text)
    search = re.search(pattern, result_string)
    return search is None


def print_time(text, start_time):
    elapsed_time = time.time() - start_time
    # 时间格式化
    elapsed_time = round(elapsed_time, 2)
    QMessageBox.information("Notice", f"{text}:{elapsed_time}s")


def open_folder(path):
    sys = platform.system()
    if sys == "Windows":
        os.startfile(path)
    elif sys == "Linux":
        subprocess.Popen(['xdg-open', path])
    elif sys == "Darwin":
        subprocess.Popen(['open', path])
    else:
        pass


def create_error_star_dict(key, original, translation, trait4O, trait4T):
    return {
        "key": key,
        "original": original,
        "translation": translation,
        "trait4O": trait4O,
        "trait4T": trait4T,
    }
