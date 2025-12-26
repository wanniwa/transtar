from __future__ import annotations

import wjson
import os
import re
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtWidgets import QMessageBox

from app.common.constant import FileType, ActionType
from app.core.HandlerFactory import HandlerFactory
from app.core.handlers.TransContext import TransContext
from app.common.config import appConfig
from app.core.requester.LLMRequester import LLMRequester
from app.core.requester.Tokener import Tokener
from app.core.TransBase import TransBase

from qfluentwidgets import InfoBar

from app.common.utils import trans_util, file_util, notify_util
from app.common.window_manager import get_window


def extract(mod_path: str) -> None:
    i18n_language = None
    i18n_language_flag = appConfig.i18n_source_flag.value
    if i18n_language_flag:
        i18n_language = appConfig.source_language.value
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
    i18n_language_flag = appConfig.i18n_source_flag.value
    if i18n_language_flag:
        i18n_language = appConfig.source_language.value

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
    """
    翻译入口：
    - google / deepl 仍然走单条翻译（保持原有逻辑）
    - 其它模型走新的 LLMRequester 管线，按批次组包 + Token 预估
    - 平台配置来源：PlatformInterface 保存的 platforms / trans_platform
    """
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
    # 读取平台配置（platforms信息从trans_config.json，其他配置从appConfig）
    from app.common.config import appConfig, load_config
    from app.common.setting import TRANS_CONFIG_FILE
    
    cfg = load_config(str(TRANS_CONFIG_FILE.absolute()))
    platforms = cfg.get("platforms", {})
    trans_tag = appConfig.trans_platform.value or "google"
    platform = platforms.get(trans_tag, platforms.get("google", {}))

    # 从 appConfig 读取任务配置
    split_mode = (appConfig.task_split_mode.value or "token").lower()
    split_token_limit = int(appConfig.task_split_token_limit.value)
    token_reserve = int(appConfig.task_token_reserve.value)
    split_count_limit = int(appConfig.task_split_count_limit.value)
    concurrency = int(appConfig.task_concurrency.value)
    request_timeout = int(appConfig.task_request_timeout.value)
    max_rounds = int(appConfig.task_max_rounds.value)

    api_format = (platform.get("api_format") or "").lower()
    use_simple_provider = api_format in ("google", "deepl")
    
    # Google/DeepL 不支持批量API，每个请求只能翻译1条
    # 但可以用多线程并发发送多个单条请求
    if use_simple_provider:
        batch_size = 1
    
    requester = None if use_simple_provider else LLMRequester()
    tokener = Tokener() if not use_simple_provider else None
    
    # 发送配置信息到看板（Google/DeepL 也可以用并发）
    platform_name = platform.get('name', trans_tag)
    if hasattr(thread, 'config_signal'):
        thread.config_signal.emit(platform_name, concurrency)
    
    # 打印翻译配置信息
    print(f"\n{'='*60}")
    print(f"翻译配置:")
    print(f"  平台: {trans_tag} ({platform_name})")
    print(f"  模式: {'简单翻译 (Google/DeepL)' if use_simple_provider else 'LLM批量翻译'}")
    if use_simple_provider:
        print(f"  翻译方式: 逐条翻译 (每个请求1条)")
        print(f"  并发数: {concurrency} {'(单线程)' if concurrency <= 1 else f'(多线程: {concurrency} workers)'}")
    else:
        print(f"  切分模式: {split_mode}")
        if split_mode == "token":
            print(f"  Token限制: {split_token_limit} (预留: {token_reserve})")
        else:
            print(f"  条目限制: {split_count_limit}")
        print(f"  并发数: {concurrency} {'(单线程)' if concurrency <= 1 else f'(多线程: {concurrency} workers)'}")
        print(f"  请求超时: {request_timeout}秒")
        print(f"  最大重试: {max_rounds}轮")
    print(f"{'='*60}\n")

    # 为 LLM 请求构造统一的 system prompt
    base_prompt = appConfig.task_prompt.value or "You are a professional Stardew Valley mod translator."
    source_lang = appConfig.source_language.value or "en"
    target_lang = appConfig.to_language.value or "zh-CN"
    llm_system_prompt = (
        f"{base_prompt}\n"
        f"Translate from {source_lang} to {target_lang}.\n"
        "保持占位符、标记、换行格式不变（例如 [LocalizedText ...]、$q/$r、%item...%% 等）。\n"
        "\n"
        "【重要】输出要求:\n"
        "- 只输出翻译后的文本，每行一个译文\n"
        "- 不要添加任何解释、说明、标题或额外内容\n"
        "- 不要添加序号、标记或格式符号\n"
        "- 按输入顺序返回译文"
    )

    # 将平台配置映射到 LLMRequester 需要的参数
    def build_platform_config(pf: dict):
        fmt = (pf.get("api_format") or "").lower()
        target_platform = "openai"
        if fmt == "gemini":
            target_platform = "gemini"
        elif fmt in ("anthropic", "claude"):
            target_platform = "anthropic"
        elif fmt == "dashscope":
            target_platform = "dashscope"
        # 其它（OpenAI 兼容）保持 openai
        return {
            "target_platform": target_platform,
            "api_url": pf.get("api_url"),
            "api_key": pf.get("api_key"),
            "api_format": pf.get("api_format"),
            "model_name": pf.get("model"),
            "request_timeout": request_timeout,
            "temperature": pf.get("temperature", 1.0),
            "top_p": pf.get("top_p", 1.0),
            "presence_penalty": pf.get("presence_penalty", 0.0),
            "frequency_penalty": pf.get("frequency_penalty", 0.0),
            "extra_body": pf.get("extra_body", {}),
            "think_switch": pf.get("think_switch"),
            "think_depth": pf.get("think_depth"),
            "thinking_budget": pf.get("thinking_budget"),
        }

    platform_config_cache = build_platform_config(platform) if not use_simple_provider else platform

    # 解析翻译结果（每行一个译文）
    def parse_translations(resp_text: str, expected_count: int) -> list:
        if not resp_text:
            return []
        
        # 尝试从 <textarea> 提取
        match = re.search(r"<textarea[^>]*>(.*?)</textarea>", resp_text, re.DOTALL | re.IGNORECASE)
        if match:
            block = match.group(1).strip()
        else:
            # 没有 <textarea> 标签，直接使用全文
            block = resp_text.strip()
        
        # 按行分割，每行一个译文，过滤空行
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        
        # 行数匹配检查和处理
        if len(lines) == expected_count:
            return lines
        elif len(lines) > expected_count:
            print(f"    警告: 期望 {expected_count} 行，返回 {len(lines)} 行（使用前 {expected_count} 行）")
            return lines[:expected_count]
        else:
            print(f"    警告: 期望 {expected_count} 行，只返回 {len(lines)} 行")
            print(f"    返回内容预览: {block[:200]}...")
            return lines

    # 发送一批待翻译内容
    def send_batch(batch_items: list, content_ref: list, progress_counter: list, lock: threading.Lock | None = None):
        nonlocal real_trans_num
        if not batch_items or not thread.running:
            return
        
        # 组装 user 内容（每行一个原文）
        user_lines = []
        for _, item in batch_items:
            original_text = item.get('original', '')
            user_lines.append(original_text)
        user_content = "\n".join(user_lines)
        messages = [{"role": "user", "content": user_content}]

        # 发送
        skip, _, resp, prompt_tokens, completion_tokens = requester.sent_request(
            messages, llm_system_prompt, platform_config_cache
        )
        if skip:
            return
        
        # 解析翻译结果（返回译文列表）
        translations = parse_translations(resp, len(batch_items))

        # 应用结果并更新进度（按索引对应）
        for i, (idx_in_content, _) in enumerate(batch_items):
            if i < len(translations) and translations[i]:
                translated = translations[i]
                if lock:
                    with lock:
                        content_ref[idx_in_content]["translation"] = translated
                        real_trans_num += 1
                        progress_counter[0] += 1
                        thread.progress_signal.emit(progress_counter[0])
                else:
                    content_ref[idx_in_content]["translation"] = translated
                    real_trans_num += 1
                    progress_counter[0] += 1
                    thread.progress_signal.emit(progress_counter[0])

    # 主循环
    file_index = 0
    for file in json_files:
        file_index += 1
        with open(file, 'r', encoding='utf-8') as f:
            content = wjson.load(f)
            print(f"\n处理文件 [{file_index}/{len(json_files)}]: {os.path.basename(file)}")
            # 多轮尝试，直到达到最大轮次或全部翻译完成
            for round_idx in range(max_rounds):
                batch = {}
                llm_batches = []
                if round_idx > 0:
                    print(f"  重试轮次: {round_idx + 1}/{max_rounds}")
                try:
                    # 收集需要翻译的条目
                    simple_items = []  # Google/DeepL 的待翻译列表：[(index, original), ...]
                    
                    for index, item in enumerate(content):
                        translation = item['translation']
                        original = item['original']

                        # 需要翻译的条目
                        if translation is None or translation == original:
                            if use_simple_provider:
                                simple_items.append((index, original))
                            else:
                                # LLM 模式：按配置切分
                                llm_batch = [] if not llm_batches else llm_batches[-1]
                                # 若前一批已确定，不重复使用
                                if llm_batches == [] or llm_batch is not None and len(llm_batch) == 0:
                                    pass
                                llm_batches.append([]) if (llm_batches == [] or llm_batch is None) else None
                                llm_batch = llm_batches[-1]
                                llm_batch.append((index, item))

                                def need_flush():
                                    if split_mode == "count":
                                        return len(llm_batch) >= split_count_limit
                                    # token 模式（每行一个原文）
                                    user_lines = [
                                        it.get('original', '')
                                        for _, it in llm_batch
                                    ]
                                    estimate_messages = [{"role": "user", "content": "\n".join(user_lines)}]
                                    est_tokens = tokener.calculate_tokens(estimate_messages, llm_system_prompt)
                                    return est_tokens > max(split_token_limit - token_reserve, 1)

                                if need_flush():
                                    # 前一批满了，重新开新批
                                    llm_batch.pop()  # remove last added
                                    if llm_batch:
                                        pass
                                    else:
                                        llm_batches.pop()
                                    # 新批只放当前
                                    llm_batches.append([(index, item)])
                        else:
                            # 已翻译的条目，直接计数
                            current_file_num += 1
                            thread.progress_signal.emit(current_file_num)
                    
                    # 检查停止标志
                    if not thread.running:
                        with open(file, 'w', encoding='utf-8') as f1:
                            wjson.dump(content, f1)
                        return real_trans_num

                    # 处理 Google/DeepL 翻译（支持并发）
                    if use_simple_provider and simple_items:
                        print(f"  待翻译条目: {len(simple_items)} 条")
                        
                        # 定义单条翻译函数
                        def translate_single(item_tuple, content_ref, progress_counter, lock=None):
                            # 检查停止标志
                            if not thread.running:
                                return 0
                            
                            idx, text = item_tuple
                            translated = trans_util.modTrans(text, platform)
                            
                            if lock:
                                with lock:
                                    content_ref[idx]['translation'] = translated
                                    progress_counter[0] += 1
                                    thread.progress_signal.emit(progress_counter[0])
                            else:
                                content_ref[idx]['translation'] = translated
                                progress_counter[0] += 1
                                thread.progress_signal.emit(progress_counter[0])
                            return 1
                        
                        # 进度计数器（使用列表以便在闭包中修改）
                        progress_counter = [current_file_num]
                        
                        # 根据并发设置选择处理方式
                        if concurrency <= 1:
                            print(f"  [单线程模式] 逐条翻译")
                            for item in simple_items:
                                if not thread.running:
                                    print(f"  翻译已停止")
                                    break
                                result = translate_single(item, content, progress_counter)
                                real_trans_num += result
                        else:
                            workers = concurrency
                            if workers <= 0:
                                workers = max(1, min((os.cpu_count() or 4), 6))
                            print(f"  [多线程模式] 使用 {workers} 个线程并发翻译")
                            
                            lock = threading.Lock()
                            with ThreadPoolExecutor(max_workers=workers) as pool:
                                futures = [pool.submit(translate_single, item, content, progress_counter, lock) for item in simple_items]
                                completed = 0
                                for future in as_completed(futures):
                                    result = future.result()
                                    if result > 0:
                                        completed += 1
                                        real_trans_num += result
                                        if completed % 10 == 0 or completed == len(futures):
                                            print(f"    翻译进度: {completed}/{len(futures)}")
                                    
                                    # 检查停止标志
                                    if not thread.running:
                                        print(f"  翻译已停止，已完成 {completed}/{len(simple_items)} 条")
                                        break
                        
                        # 更新当前文件进度
                        current_file_num = progress_counter[0]
                    else:
                        # 执行批处理（可并发）
                        if llm_batches:
                            # 清理空批
                            llm_batches = [b for b in llm_batches if b]
                            # 进度计数器
                            progress_counter = [current_file_num]
                            
                            if concurrency <= 1:
                                print(f"[单线程模式] 处理 {len(llm_batches)} 个批次")
                                for b in llm_batches:
                                    if not thread.running:
                                        print(f"  翻译已停止")
                                        break
                                    send_batch(b, content, progress_counter)
                            else:
                                workers = concurrency
                                if workers <= 0:
                                    workers = max(1, min((os.cpu_count() or 4), 6))
                                print(f"[多线程模式] 使用 {workers} 个线程并发处理 {len(llm_batches)} 个批次")
                                lock = threading.Lock()
                                with ThreadPoolExecutor(max_workers=workers) as pool:
                                    futures = [pool.submit(send_batch, b, content, progress_counter, lock) for b in llm_batches]
                                    completed = 0
                                    for future in as_completed(futures):
                                        if not thread.running:
                                            print(f"  翻译已停止，已完成 {completed}/{len(futures)} 批次")
                                            break
                                        future.result()
                                        completed += 1
                                        print(f"  批次进度: {completed}/{len(futures)}")
                            
                            # 更新当前文件进度
                            current_file_num = progress_counter[0]

                except Exception as e:
                    with open(file, 'w', encoding='utf-8') as f1:
                        wjson.dump(content, f1)
                    raise e

                # 检查是否还有未翻译
                remaining = any((it['translation'] is None or it['translation'] == it['original']) for it in content)
                if not remaining:
                    break

            # 保存文件
            with open(file, 'w', encoding='utf-8') as f1:
                wjson.dump(content, f1)
            print(f"  完成文件: {os.path.basename(file)}")
    
    print(f"\n{'='*60}")
    print(f"翻译完成! 共翻译 {real_trans_num} 条")
    print(f"{'='*60}\n")
    return real_trans_num


def process_old_common(mod_path, old_folder_path, old_trans_folder_path):
    if appConfig.i18n_source_flag.value:
        i18n_file_name = appConfig.source_language.value
    else:
        i18n_file_name = "default"
    try:
        oldNoTransDicts = process_dict(old_folder_path, i18n_file_name)
    except Exception as e:
        notify_util.notify_error(e, old_folder_path)
        return
    try:
        oldTransDicts = process_dict(old_trans_folder_path, appConfig.to_language.value)
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
                key = noTransdict['key'].replace(i18n_file_name, appConfig.to_language.value)
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
