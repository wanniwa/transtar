import wjson
import os
import shutil

from PySide6.QtWidgets import QMessageBox

from app.common.constant import FileType, ActionType
from app.core.handler_factory import HandlerFactory
from app.core.handlers.trans_context import TransContext
from ..common.config import cfg

from qfluentwidgets import InfoBar

from ..common.utils import trans_util, file_util, notify_util
from ..common.window_manager import get_window


def extract(mod_path: str) -> None:
    i18n_language = None
    i18n_language_flag = cfg.i18n_source_flag.value
    if i18n_language_flag:
        i18n_language = cfg.source_language.value
    files_by_type = file_util.get_files_by_type(mod_path, i18n_language)
    if not files_by_type:
        files_by_type = {}

    if os.path.exists(file_util.get_error_dict_path(mod_path)):
        shutil.rmtree(file_util.get_error_dict_path(mod_path), ignore_errors=True)

    # Process non-I18N files first
    for file_type, files in list(files_by_type.items()):
        if file_type != FileType.I18N:
            context = TransContext(mod_path, True, False, ActionType.EXTRACT, file_type, files_by_type)
            handler = HandlerFactory.get_trans_handler(file_type)(context)
            handler.batch_handle(files)
            handler.create_dict_file()

    # Finally process all I18N files together
    if FileType.I18N in files_by_type:
        context = TransContext(mod_path, True, False, ActionType.EXTRACT, FileType.I18N, files_by_type)
        handler = HandlerFactory.get_trans_handler(FileType.I18N)(context)
        handler.batch_handle(files_by_type[FileType.I18N])
        handler.create_dict_file()

    InfoBar.success(get_window().tr("Success"), get_window().tr(f"Extract completed"), duration=3000,
                    parent=get_window())
    file_util.open_folder(file_util.get_dict_path(mod_path))


def generate(mod_path: str) -> None:
    """Generate translations for mod files"""
    i18n_language = None
    i18n_language_flag = cfg.i18n_source_flag.value
    if i18n_language_flag:
        i18n_language = cfg.source_language.value

    files_by_type = file_util.get_files_by_type(mod_path, i18n_language)
    if not files_by_type:
        return

    if os.path.exists(file_util.get_error_dict_path(mod_path)):
        shutil.rmtree(file_util.get_error_dict_path(mod_path), ignore_errors=True)
    if os.path.exists(file_util.get_out_path(mod_path)):
        shutil.rmtree(file_util.get_out_path(mod_path), ignore_errors=True)

    for file_type, files in files_by_type.items():
        context = TransContext(mod_path, False, True, ActionType.GENERATE, file_type, files_by_type)
        handler = HandlerFactory.get_trans_handler(file_type)(context)
        handler.batch_handle(files)
        handler.create_error_dict_file()

    file_util.open_folder(os.path.dirname(mod_path))


def validate(mod_path):
    # Delete all files in the folder
    if os.path.exists(file_util.get_error_dict_path(mod_path)):
        shutil.rmtree(file_util.get_error_dict_path(mod_path), ignore_errors=True)
    json_files = file_util.get_all_json_files(file_util.get_dict_path(mod_path))
    total = 0
    total_file_num = 0
    current_file_num = 0

    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
            total_file_num += len(content)
    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
            error_dict_list = []
            for item in content:
                translation_trait = trans_util.trait(item['translation'])
                original_trait = trans_util.trait(item['original'])
                if translation_trait != original_trait:
                    error_dict_list.append(
                        trans_util.create_error_star_dict(item['key'], item['original'], item['translation'],
                                                          original_trait, translation_trait))
                current_file_num += 1
            if error_dict_list:
                total += len(error_dict_list)
                if not os.path.exists(file_util.get_error_dict_path(mod_path)):
                    os.makedirs(file_util.get_error_dict_path(mod_path))
                with open(file_util.get_error_dict_path(mod_path) + "/" + os.path.basename(file), 'w',
                          encoding='utf-8') as f1:
                    wjson.dump(error_dict_list, f1)
    if total > 0:
        InfoBar.success(get_window().tr("Success"), get_window().tr(f"Task completed, total {total} error translation"),
                        duration=3000,
                        parent=get_window())
        trans_util.open_folder(file_util.get_error_dict_path(mod_path))
    else:
        InfoBar.success(get_window().tr("Success"), get_window().tr(f"Congratulations, no error translation!"),
                        duration=3000,
                        parent=get_window())


def import_from_error(mod_path):
    if not os.path.exists(file_util.get_error_dict_path(mod_path)):
        InfoBar.warning(get_window().tr("Warning"), get_window().tr("No error dicts"), duration=3000,
                        parent=get_window())
        return
    errorDictPaths = file_util.get_json_files_in_directory(file_util.get_error_dict_path(mod_path))
    for error_dict_path in errorDictPaths:
        filename = os.path.basename(error_dict_path)
        dict_json_path = os.path.join(file_util.get_dict_path(mod_path), filename)
        if os.path.exists(dict_json_path):
            with open(error_dict_path, 'r', encoding='utf-8') as error_f:
                error_dict = wjson.load(error_f)
                with open(dict_json_path, 'r', encoding='utf-8') as dict_f:
                    dict_json = wjson.load(dict_f)
                    dict_map = {item['key']: item for item in dict_json}
                    for item in error_dict:
                        dict_map[item['key']]['translation'] = item['translation']
                    with open(dict_json_path, 'w', encoding='utf-8') as dict_out_f:
                        wjson.dump(dict_json, dict_out_f)
    InfoBar.success(get_window().tr("Error"), get_window().tr("import success, you can validate again"), duration=3000,
                    parent=get_window())


def translate(mod_path, thread, batch_size):
    if os.path.exists(file_util.get_error_dict_path(mod_path)):
        shutil.rmtree(file_util.get_error_dict_path(mod_path), ignore_errors=True)
    json_files = file_util.get_all_json_files(file_util.get_dict_path(mod_path))
    if len(json_files) == 0:
        return 0
    total_file_num = 0
    current_file_num = 0
    real_trans_num = 0
    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
            total_file_num += len(content)
    thread.total_entries_signal.emit(total_file_num)
    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
            batch = {}
            try:
                for index, item in enumerate(content):
                    translation = item['translation']
                    original = item['original']
                    if translation is None or translation == original:
                        batch[index] = original
                        if len(batch) == batch_size:
                            translations = trans_util.batch_translate(batch.values())
                            for i, (key, translated) in enumerate(zip(batch.keys(), translations)):
                                content[key]['translation'] = translated
                            real_trans_num += len(batch)
                            batch = {}
                    current_file_num += 1
                    thread.progress_signal.emit(current_file_num)
                    if not thread.running:
                        with open(file, 'w', encoding='utf-8') as f1:
                            wjson.dump(content, f1)
                        return real_trans_num
                if batch:
                    translations = trans_util.batch_translate(batch.values())
                    for key, translated in zip(batch.keys(), translations):
                        content[key]['translation'] = translated
                    real_trans_num += len(batch)
            except Exception as e:
                with open(file, 'w', encoding='utf-8') as f1:
                    wjson.dump(content, f1)
                raise e
            with open(file, 'w', encoding='utf-8') as f1:
                wjson.dump(content, f1)
    return real_trans_num


def process_old_common(mod_path, old_folder_path, old_trans_folder_path):
    if cfg.i18n_source_flag.value:
        i18n_file_name = cfg.source_language.value
    else:
        i18n_file_name = "default"
    try:
        oldNoTransDicts = process_dict(old_folder_path, i18n_file_name)
    except Exception as e:
        notify_util.notify_error(e, old_folder_path)
        return
    try:
        oldTransDicts = process_dict(old_trans_folder_path, cfg.to_language.value)
    except Exception as e:
        notify_util.notify_error(e, old_trans_folder_path)
        return
    if oldNoTransDicts is None or oldTransDicts is None:
        QMessageBox.information(None, "notice",
                                f"No old dicts can Extract, please check '{old_folder_path}' and '{old_trans_folder_path}'")
        return
    for k, v in oldNoTransDicts.items():
        transDicts = oldTransDicts.get(k, [])
        transDictsMap = {}
        for transDict in transDicts:
            transDictsMap[transDict['key']] = transDict
        for noTransdict in v:
            if k == FileType.I18N:
                key = noTransdict['key'].replace(i18n_file_name, cfg.to_language.value)
            else:
                key = noTransdict['key']
            transDict = transDictsMap.get(key, None)
            if transDict is None:
                continue
            noTransdict['translation'] = transDict['original']
        if len(v) > 0:
            dict_file_path = file_util.get_dict_path(mod_path) + "/" + k.file_name
            dict_json = wjson.dumps(v, indent=4)
            with open(dict_file_path, 'w', encoding='utf-8') as file:
                file.write(dict_json)
    try:
        extract(mod_path)
    except Exception as e:
        print(e)
        notify_util.notify_error(e, mod_path)


def process_dict(mod_path, i18n_file_name):
    files_by_type = file_util.get_files_by_type(mod_path, i18n_file_name)
    if not files_by_type:
        return
    result = {}
    for file_type, files in files_by_type.items():
        context = TransContext(mod_path, True, False, ActionType.EXTRACT, file_type, files_by_type)
        handler = HandlerFactory.get_trans_handler(file_type)(context)
        handler.batch_handle(files)
        if len(context.star_dicts) > 0:
            result[file_type] = context.star_dicts
    return result
