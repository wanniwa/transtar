import os
from typing import Optional

import hjson

from app.common.utils.file_util import get_all_json_files


class ManifestInfo:
    def __init__(self, name: str = "", nexus_id: str = "", file_path: str = ""):
        self.name = name
        self.nexus_id = nexus_id
        self.file_path = file_path

    def __str__(self):
        if self.nexus_id:
            return f"{self.nexus_id} {self.name}"
        return self.name


def find_manifest_files(folder_path: str) -> list[str]:
    """查找目录下所有的manifest.json文件"""
    all_json_files = get_all_json_files(folder_path)
    return [f for f in all_json_files if os.path.basename(f).lower() == 'manifest.json']


def parse_manifest(file_path: str) -> Optional[ManifestInfo]:
    """解析manifest.json文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = hjson.load(f)
            info = ManifestInfo(file_path=file_path)

            # 获取mod名称
            if 'Name' in data:
                info.name = data['Name']

            # 获取Nexus ID
            if 'UpdateKeys' in data:
                for key in data['UpdateKeys']:
                    if 'Nexus:' in key:
                        nexus_id = key.split(':')[1]
                        # 只有当nexus_id是正整数时才设置
                        try:
                            id_num = int(nexus_id)
                            if id_num > 0:
                                info.nexus_id = nexus_id
                                break
                        except ValueError:
                            continue

            return info
    except Exception as e:
        print(f"Error parsing manifest {file_path}: {e}")
        return None


def get_mod_infos(folder_path: str) -> list[ManifestInfo]:
    """获取所有manifest信息"""
    manifest_files = find_manifest_files(folder_path)
    infos = []

    # 首先尝试找有nexus_id的manifest
    for file_path in manifest_files:
        info = parse_manifest(file_path)
        if info and info.nexus_id:  # 只收集有nexus_id的
            infos.append(info)

    # 如果没有找到任何带nexus_id的manifest，则收集所有有效的manifest
    if not infos:
        for file_path in manifest_files:
            info = parse_manifest(file_path)
            if info and (info.name or info.nexus_id):  # 确保至少有name或nexus_id
                infos.append(info)

    return infos
