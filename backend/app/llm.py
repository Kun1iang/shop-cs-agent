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
        completion = client.chat.completions.create(
            model=self.settings.deepseek_model,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            temperature=0.3,
        )
        content = completion.choices[0].message.content
        if not content or not content.strip():
            raise LLMResponseError("模型没有返回有效内容")
        return content.strip()


def get_llm_client() -> DeepSeekClient:
    from app.config import settings

    return DeepSeekClient(settings)

