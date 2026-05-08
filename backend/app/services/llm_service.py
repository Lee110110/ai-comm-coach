import json
import logging
from dataclasses import dataclass
from openai import AsyncOpenAI, APIError, AuthenticationError
from fastapi import HTTPException, status

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int


class LLMService:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.default_model = settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS

    async def call(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        json_mode: bool = True,
    ) -> LLMResponse:
        kwargs = dict(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or self.max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except AuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI 服务认证失败，请检查 API Key 配置",
            )
        except APIError as e:
            logger.error(f"LLM API error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI 服务暂时不可用：{str(e)[:200]}",
            )

        content = response.choices[0].message.content or ""
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    async def call_json(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> tuple[dict, int, int]:
        response = await self.call(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        try:
            data = json.loads(response.content)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON, attempting repair")
            data = self._repair_json(response.content)

        return data, response.input_tokens, response.output_tokens

    def _repair_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM response", "raw": text[:500]}


llm_service = LLMService()
