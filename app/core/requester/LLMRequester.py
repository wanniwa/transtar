from app.core.requester.LocalLLMRequester import LocalLLMRequester
from app.core.requester.CohereRequester import CohereRequester
from app.core.requester.GeminiRequester import GeminiRequester
from app.core.requester.AnthropicRequester import AnthropicRequester
from app.core.requester.AmazonbedrockRequester import AmazonbedrockRequester
from app.core.requester.OpenaiRequester import OpenaiRequester
from app.core.requester.DashscopeRequester import DashscopeRequester

# 接口请求器
class LLMRequester():
    def __init__(self) -> None:
        pass

    # 分发请求
    def sent_request(self, messages: list[dict], system_prompt: str, platform_config: dict) -> tuple[bool, str, str, int, int]:
        # 获取平台参数
        target_platform = platform_config.get("target_platform")
        api_format = platform_config.get("api_format")

        # 发起请求
        if target_platform == "cohere":
            cohere_requester = CohereRequester()
            skip, response_think, response_content, prompt_tokens, completion_tokens = cohere_requester.request_cohere(
                messages,
                system_prompt,
                platform_config,
            )
        elif target_platform == "gemini" or (target_platform.startswith("custom_platform_") and api_format == "Gemini"):
            gemini_requester = GeminiRequester()
            skip, response_think, response_content, prompt_tokens, completion_tokens = gemini_requester.request_gemini(
                messages,
                system_prompt,
                platform_config,
            )
        elif target_platform == "anthropic" or (target_platform.startswith("custom_platform_") and api_format == "Anthropic"):
            anthropic_requester = AnthropicRequester()
            skip, response_think, response_content, prompt_tokens, completion_tokens = anthropic_requester.request_anthropic(
                messages,
                system_prompt,
                platform_config,
            )
        elif target_platform == "amazonbedrock":
            amazonbedrock_requester = AmazonbedrockRequester()
            skip, response_think, response_content, prompt_tokens, completion_tokens = amazonbedrock_requester.request_amazonbedrock(
                messages,
                system_prompt,
                platform_config,
            )
        elif target_platform == "dashscope":
            dashscope_requester = DashscopeRequester()
            skip, response_think, response_content, prompt_tokens, completion_tokens = dashscope_requester.request_openai(
                messages,
                system_prompt,
                platform_config,
            )
        else:
            openai_requester = OpenaiRequester()
            skip, response_think, response_content, prompt_tokens, completion_tokens = openai_requester.request_openai(
                messages,
                system_prompt,
                platform_config,
            )

        return skip, response_think, response_content, prompt_tokens, completion_tokens
