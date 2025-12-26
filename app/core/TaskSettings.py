# coding:utf-8
"""
任务设置默认配置
"""

TASK_SETTINGS_DEFAULT = {
    "task_settings": {
        "split_mode": "token",          # token / count
        "split_token_limit": 3000,      # 单批原文 token 上限
        "token_reserve": 3000,           # 为回复预留的 token
        "split_count_limit": 20,        # 单批最大词条数（按 count 模式）
        "concurrency": 0,               # 0 表示自动（min(物理核, 6)）
        "request_timeout": 120,         # 单次请求超时秒
        "max_rounds": 1,                # 最大轮次
    }
}

