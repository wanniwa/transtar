# coding: utf-8
from pathlib import Path

# change DEBUG to False if you want to compile the code to exe
DEBUG = "__compiled__" not in globals()


YEAR = 2024
AUTHOR = "wanniwa"
VERSION = "2.0.3"
APP_NAME = "transtar"
HELP_URL = "https://www.nexusmods.com/stardewvalley/mods/20435"
REPO_URL = "https://github.com/wanniwa/transtar"
FEEDBACK_URL = "https://github.com/wanniwa/transtar/issues"
DOC_URL = "https://www.nexusmods.com/stardewvalley/mods/20435"

CONFIG_FOLDER = Path('AppData').absolute()
CONFIG_FILE = CONFIG_FOLDER / "config.json"
