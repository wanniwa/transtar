# coding:utf-8
import sys
from enum import Enum

from PySide6.QtCore import QLocale
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, Theme, ConfigSerializer, RangeConfigItem, RangeValidator)

from .setting import CONFIG_FILE
from .constant import LANGUAGES

models = ['google', 'deepl', 'gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-2024-04-09', 'gpt-4o', 'gpt-4o-mini']


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
    ENGLISH = QLocale(QLocale.Language.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    # TODO: ADD YOUR CONFIG GROUP HERE
    # 个性化配置
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # 翻译配置
    """ Config of application """
    i18n_ignore_cp = ConfigItem("Translation", "i18n_ignore_cp", True, BoolValidator())
    i18n_source_flag = ConfigItem("Translation", "i18n_source_flag", False, BoolValidator())
    trans_model = OptionsConfigItem("Translation", "trans_model", "google", OptionsValidator(models))
    ai_batch_size = RangeConfigItem("Translation", "ai_batch_size", 5, RangeValidator(1, 20))
    ai_prompt = ConfigItem("Translation", "ai_prompt",
                           "You are currently a professional Stardew Valley mod translator. ", None)
    api_key = ConfigItem("Translation", "api_key", "", None)

    source_language = OptionsConfigItem(
        "Translation", "source_language", LANGUAGES['English'], OptionsValidator(LANGUAGES.values()), restart=False)
    to_language = OptionsConfigItem(
        "Translation", "to_language", LANGUAGES['Chinese'], OptionsValidator(LANGUAGES.values()), restart=False)

    # software update
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())


cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load(str(CONFIG_FILE.absolute()), cfg)
