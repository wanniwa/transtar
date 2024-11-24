from typing import Dict, Any
import requests
from abc import ABC, abstractmethod

class APIError(Exception):
    """基础API异常类"""
    pass

class BaseAPI(ABC):
    """API基类"""
    
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        pass

    def make_request(self, method: str, url: str, **kwargs) -> Any:
        """发送API请求"""
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.get_headers(),
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {str(e)}")
