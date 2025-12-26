import tiktoken


class Tokener:
    """Token计算器，用于计算消息和文本的Token数量"""

    def __init__(self) -> None:
        pass

    def num_tokens_from_messages(self, messages: list) -> int:
        """
        计算消息列表内容的tokens数量
        
        Parameters
        ----------
        messages: list
            消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            
        Returns
        -------
        int
            Token数量
        """
        encoding = tiktoken.get_encoding("o200k_base")

        tokens_per_message = 3
        tokens_per_name = 1
        num_tokens = 0
        
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                # 如果value是字符串类型才计算tokens，否则跳过
                if isinstance(value, str):
                    num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    def num_tokens_from_str(self, text: str) -> int:
        """
        计算字符串内容的tokens数量
        
        Parameters
        ----------
        text: str
            要计算的文本
            
        Returns
        -------
        int
            Token数量
        """
        encoding = tiktoken.get_encoding("o200k_base")

        if isinstance(text, str):
            num_tokens = len(encoding.encode(text))
        else:
            num_tokens = 0

        return num_tokens

    def calculate_tokens(self, messages: list, system_prompt: str) -> int:
        """
        根据输入的消息和系统提示词，计算tokens消耗并返回
        
        Parameters
        ----------
        messages: list
            消息列表
        system_prompt: str
            系统提示词
            
        Returns
        -------
        int
            总Token数量
        """
        tokens1 = self.num_tokens_from_messages(messages) if messages else 0
        tokens_text1 = self.num_tokens_from_str(system_prompt) if system_prompt else 0
        return tokens1 + tokens_text1

