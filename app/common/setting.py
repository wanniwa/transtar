# coding: utf-8
from pathlib import Path
import appdirs

# change DEBUG to False if you want to compile the code to exe
DEBUG = "__compiled__" not in globals()


YEAR = 2024
AUTHOR = "wanniwa"
VERSION = "2.1.0"
APP_NAME = "transtar"
HELP_URL = "https://www.nexusmods.com/stardewvalley/mods/20435"
REPO_URL = "https://github.com/wanniwa/transtar"
FEEDBACK_URL = "https://github.com/wanniwa/transtar/issues"
DOC_URL = "https://www.nexusmods.com/stardewvalley/mods/20435"


CONFIG_FOLDER = appdirs.user_config_dir("transtar")
# 如果配置文件夹不存在则创建
Path(CONFIG_FOLDER).mkdir(parents=True, exist_ok=True)

CONFIG_FILE = Path(CONFIG_FOLDER).joinpath("config.json")
