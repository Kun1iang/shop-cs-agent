from openai import OpenAI

from app.config import Settings


class LLMUnavailableError(Exception):
    pass


class LLMResponseError(Exception):
    pass


class DeepSeekClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def reply(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> str:
        completion = self.complete(system_prompt, messages)
        content = completion.content
        if not content or not content.strip():
            raise LLMResponseError("模型没有返回有效内容")
        return content.strip()

    def complete(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict] | None = None,
    ):
        if not self.settings.deepseek_api_key:
            raise LLMUnavailableError(
                "DeepSeek API Key 尚未配置，请在 backend/.env 中设置 "
                "SHOP_DEEPSEEK_API_KEY"
            )

        client = OpenAI(
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.deepseek_base_url,
            timeout=self.settings.deepseek_timeout_seconds,
        )
        request: dict = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            "temperature": 0.3,
        }
        if tools:
            request["tools"] = tools
            request["tool_choice"] = "auto"

        completion = client.chat.completions.create(**request)
        return completion.choices[0].message


def get_llm_client() -> DeepSeekClient:
    from app.config import settings

    return DeepSeekClient(settings)

