from typing import List, Dict
from ...common.config import appConfig
from ..base import BaseAPI
from .exceptions import ParatranzAPIError
import wjson
import os


class ParatranzAPI(BaseAPI):
    """Paratranz API实现"""
    BASE_URL = "https://paratranz.cn/api"

    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        if not appConfig.paratranz_token.value:
            raise ParatranzAPIError("Paratranz token not configured")
        return {
            'Authorization': appConfig.paratranz_token.value,
        }

    def _get_project_id(self) -> str:
        """获取项目ID"""
        if not appConfig.paratranz_project_id.value:
            raise ParatranzAPIError("Paratranz project ID not configured")
        return appConfig.paratranz_project_id.value

    def get_project_files(self) -> List[dict]:
        """获取项目文件列表"""
        project_id = self._get_project_id()
        url = f"{self.BASE_URL}/projects/{project_id}/files"
        result = self.make_request('GET', url)
        print("\nGet project files response:")
        print(wjson.dumps(result))
        return result

    def upload_file(self, file_path: str, folder: str = "") -> dict:
        """上传文件"""
        project_id = self._get_project_id()
        url = f"{self.BASE_URL}/projects/{project_id}/files/upload"
        files = {'file': open(file_path, 'rb')}
        data = {'folder': folder} if folder else {}
        return self.make_request('POST', url, files=files, data=data)

    def get_project_strings(self, file_id: int, page: int = 1, page_size: int = 1000, manage: int = 1) -> dict:
        """获取项目词条的单目数据
        
        Args:
            file_id: 文件ID
            page: 页码
            page_size: 每页条数
            manage: 管理模式(1表示包含所有词条)
            
        Returns:
            包含条数据的字典
        """
        params = {
            'file': file_id,
            'page': page,
            'pageSize': page_size,
            'manage': manage
        }

        return self.make_request('GET', f"{self.BASE_URL}/projects/{self._get_project_id()}/strings", params=params)

    def get_project_all_strings(self, file_id: int, page_size: int = 1000) -> List[dict]:
        """获取项目文件的所有词条
        
        Args:
            file_id: 文件ID
            page_size: 每页条数
            
        Returns:
            所有词条数据的列表
        """
        all_strings = []
        page = 1

        while True:
            response = self.get_project_strings(
                file_id=file_id,
                page=page,
                page_size=page_size,
                manage=1
            )

            all_strings.extend(response['results'])

            if page >= response['pageCount']:
                break
            page += 1

        return all_strings

    def get_file_translation(self, file_id: int) -> List[dict]:
        """获取文件的所有翻译数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            包含所有翻译数据列表
        """
        url = f"{self.BASE_URL}/projects/{self._get_project_id()}/files/{file_id}/translation"
        print(f"\nGetting file translation:")
        print(f"URL: {url}")
        result = self.make_request('GET', url)
        print("API Response:")
        print(f"... (total {len(result)} records)")
        return result

    def create_file(self, file_path: str, folder: str = "") -> dict:
        """创建新文件"""
        project_id = self._get_project_id()
        url = f"{self.BASE_URL}/projects/{project_id}/files"

        print(f"\nCreating file:")
        print(f"URL: {url}")
        print(f"File path: {file_path}")
        print(f"Folder: {folder}")

        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'filename': os.path.basename(file_path),
                'path': folder
            }
            result = self.make_request('POST', url, files=files, data=data)
            print("API Response:")
            print(wjson.dumps(result, indent=4))
            return result

    def update_file(self, file_id: int, file_path: str) -> dict:
        """更新已有文件"""
        project_id = self._get_project_id()
        url = f"{self.BASE_URL}/projects/{project_id}/files/{file_id}"

        print(f"\nUpdating file:")
        print(f"URL: {url}")
        print(f"File ID: {file_id}")
        print(f"File path: {file_path}")

        with open(file_path, 'rb') as f:
            files = {'file': f}
            try:
                result = self.make_request('POST', url, files=files)
                print("API Response:")
                print(wjson.dumps(result, indent=4))

                # 处理 hashMatched 情况
                if isinstance(result, dict) and result.get('status') == 'hashMatched':
                    return {
                        "status": "hashMatched",
                        "revision": {
                            "insert": 0,
                            "update": 0,
                            "remove": 0
                        }
                    }
                return result
            except ParatranzAPIError as e:
                if 'hashMatched' in str(e):
                    print("File hash matched, no changes needed")
                    return {
                        "status": "hashMatched",
                        "revision": {
                            "insert": 0,
                            "update": 0,
                            "remove": 0
                        }
                    }
                raise e
