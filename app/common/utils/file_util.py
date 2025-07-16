import platform
import os
import subprocess
from typing import List, Dict

from app.common.constant import FileType


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


def get_all_json_files(folder_path: str) -> List[str]:
    """Get all JSON files in the folder and its subfolders"""
    json_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files


def get_json_files_in_directory(directory_path: str) -> List[str]:
    """Get JSON files in the specified directory (not recursive)"""
    files_list = []
    for file in os.scandir(directory_path):
        if file.is_file() and file.name.endswith('.json'):
            files_list.append(file.path)
    return files_list


def get_files_by_type(root_path: str, i18n_language: str) -> Dict[FileType, List[str]]:
    """Group files by their type"""
    files_by_type = {}
    for file_path in get_all_json_files(root_path):
        file_type = get_target_type(file_path, i18n_language)
        if file_type != FileType.UNKNOWN:
            if file_type not in files_by_type:
                files_by_type[file_type] = []
            files_by_type[file_type].append(file_path)
    return files_by_type


def get_target_type(file_path, i18n_language):
    file_folder_path = os.path.dirname(file_path)
    file_name = os.path.basename(file_path)

    if "i18n" in file_folder_path.lower():
        # Scenario 1: File name directly indicates language (i18n/zh.json, i18n/default.json)
        if i18n_language is not None:
            i18n_target_file_name = i18n_language + ".json"
        else:
            i18n_target_file_name = "default.json"
        
        if file_name == i18n_target_file_name:
            return FileType.I18N
        
        # Scenario 2: Language indicated by folder name (i18n/zh/lucy.json)
        # Get the parent folder name (should be the language folder)
        parent_folder_name = os.path.basename(file_folder_path)
        
        # Check if the parent folder is directly i18n (meaning we're in i18n/somefile.json)
        if parent_folder_name.lower() == "i18n":
            return FileType.UNKNOWN
        
        # Check if we're in a language subfolder under i18n
        grandparent_folder_path = os.path.dirname(file_folder_path)
        grandparent_folder_name = os.path.basename(grandparent_folder_path)
        
        if grandparent_folder_name.lower() == "i18n":
            # We're in i18n/language_folder/file.json structure
            if i18n_language is not None:
                # Check if the folder name matches the target language
                if parent_folder_name == i18n_language:
                    return FileType.I18N
            else:
                # If no specific language is set, check for default folder
                if parent_folder_name == "default":
                    return FileType.I18N
        
        return FileType.UNKNOWN
    elif (("[JA]" in file_folder_path or (
            "[CC]" in file_folder_path and file_name == "object.json"))
          and file_name.endswith(".json")
          and file_name != "manifest.json"):
        return FileType.JA
    elif "[BL]" in file_folder_path and file_name == "content.json":
        return FileType.BL
    elif "[STF]" in file_folder_path and file_name == "shops.json":
        return FileType.STF
    elif file_name == "content.json":
        return FileType.CP
    elif file_name.lower() == "mail.json" and "assets" not in file_folder_path.lower():
        return FileType.MAIL
    elif "[QF]" in file_folder_path and file_name == "quests.json":
        return FileType.QF
    else:
        return FileType.UNKNOWN


def get_dict_path(mod_path):
    dict_path = mod_path + " " + "dict"
    return dict_path


def get_error_dict_path(mod_path):
    return get_dict_path(mod_path) + "/error"


def get_out_path(mod_path):
    out_path = mod_path + " " + "translation"
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    return out_path


def get_relative_path(file_path, mod_path):
    replace = str(os.path.relpath(file_path, mod_path)).replace("/", "\\")
    return "\\" + replace

def get_i18n_folder(file_path):
    file_folder_path = os.path.dirname(file_path)
    i18n_folder = file_folder_path + "/i18n"
    return i18n_folder