import json
import hjson


def clean_newlines(pairs):
    result = {}
    for key, value in pairs:
        if isinstance(value, str):
            value = value.replace('\n', '')
            if value == ',':
                continue
            if value.endswith(','):
                value = value[:-1]
            if value.startswith('.') and value[1:].isdigit():
                value = float('0' + value)
        result[key] = value
    return result


def loads(content, encoding='utf-8'):
    """
    加载JSON字符串，自动处理数字格式和换行符
    :param content: JSON字符串
    :return: 解析后的对象
    """
    return hjson.loads(content, encoding, strict=False, object_pairs_hook=clean_newlines)


def load(file, encoding='utf-8'):
    """
    从文件加载JSON
    :param file: 文件对象
    :param encoding: 编码方式，默认utf-8
    :return: 解析后的对象
    """
    return hjson.load(file, encoding, strict=False, object_pairs_hook=clean_newlines)


def dump(obj, file):
    """
    将对象写入JSON文件
    :param obj: 要写入的对象（可以是字典或列表）
    :param file: 文件对象
    """

    # 转换为JSON字符串并写入
    json.dump(obj, file, ensure_ascii=False, indent=4)


def dumps(obj, indent=4):
    return json.dumps(obj, ensure_ascii=False, indent=indent)
