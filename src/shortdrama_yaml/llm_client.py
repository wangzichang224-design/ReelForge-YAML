from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .chapter_parser import Chapter
from .offline_generator import build_offline_script
from .prompts import SYSTEM_PROMPT, build_generation_prompt, build_repair_prompt


@dataclass(frozen=True)
class LLMConfig:
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.2
    max_tokens: int = 8000
    timeout_seconds: float = 120.0
    use_offline_demo: bool = True


class LLMGenerationError(RuntimeError):
    pass


class OpenAICompatibleJSONClient:
    """DeepSeek / OpenAI-compatible JSON mode client with an offline demo fallback."""

    def generate_payload(
        self,
        chapters: list[Chapter],
        *,
        title: str,
        genre: str,
        tone: str,
        target_style: str,
        shots_per_episode: int,
        config: LLMConfig,
    ) -> dict[str, Any]:
        if config.use_offline_demo or not config.api_key:
            return build_offline_script(
                chapters,
                title=title,
                genre=genre,
                tone=tone,
                shots_per_episode=shots_per_episode,
            )

        prompt = build_generation_prompt(
            chapters,
            title=title,
            genre=genre,
            tone=tone,
            target_style=target_style,
            shots_per_episode=shots_per_episode,
        )
        return self._chat_json(prompt, config=config)

    def repair_payload(
        self,
        payload: dict,
        validation_error: str,
        *,
        config: LLMConfig,
    ) -> dict[str, Any]:
        if config.use_offline_demo or not config.api_key:
            raise LLMGenerationError("离线模式无法调用模型修复 JSON。")
        prompt = build_repair_prompt(payload, validation_error)
        return self._chat_json(prompt, config=config)

    def _chat_json(self, user_prompt: str, *, config: LLMConfig) -> dict[str, Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMGenerationError("缺少 openai SDK，请先安装 requirements.txt。") from exc

        client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=config.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )
                content = response.choices[0].message.content or ""
                if not content.strip():
                    raise LLMGenerationError("模型返回空 content。")
                return robust_json_loads(content)
            except Exception as exc:  # noqa: BLE001 - surface retry context to UI
                last_error = exc
                if attempt == 2:
                    break
        raise LLMGenerationError(f"模型 JSON 生成失败：{last_error}") from last_error


def robust_json_loads(content: str) -> dict[str, Any]:
    """Parse JSON even if a model wraps it in a fenced block."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        loaded = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end < start:
            raise
        loaded = json.loads(cleaned[start : end + 1])

    if not isinstance(loaded, dict):
        raise ValueError("模型输出 JSON 根节点必须是 object。")
    return loaded
