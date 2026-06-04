from __future__ import annotations

import json
from dataclasses import dataclass, field

from .evaluator import evaluate_document
from .llm_client import LLMConfig, OpenAICompatibleJSONClient
from .schema import QualityReport, ScriptDocument


CRITIC_SYSTEM_PROMPT = """你是一位深谙爆款短剧流量密码的金牌网剧总监。
你的任务是极其挑剔地审查 AI 转化出来的短剧 YAML 剧本。

必须量化检查：
1. 黄金三秒：第 1 个 shot 是否直接出现强视觉冲突或情绪冲突。
2. 视觉可执行性：video_prompt 是否是摄影机可捕捉的动作、构图、光影，而非文学抽象词。
3. 权力翻转：本集是否发生掌控权、财富优势、心理优势的变化。
4. 骗氪钩子：结尾是否卡在真相即将揭晓、危机降临、身份暴露或反派反扑之前。

只输出 JSON object，不要 Markdown。
"""


@dataclass(frozen=True)
class CriticResult:
    passed: bool
    report: QualityReport
    critic_notes: list[str] = field(default_factory=list)
    raw_critic_payload: dict | None = None


class ScriptCritic:
    def review(
        self,
        document: ScriptDocument,
        *,
        input_chapter_count: int,
        structural_warnings: list[str] | None = None,
        client: OpenAICompatibleJSONClient | None = None,
        config: LLMConfig | None = None,
        use_llm: bool = False,
    ) -> CriticResult:
        report = evaluate_document(
            document,
            input_chapter_count=input_chapter_count,
            structural_warnings=structural_warnings,
            visual_bible=document.visual_bible,
        )
        notes = list(report.repair_suggestions)
        raw_payload = None
        if use_llm and client and config and config.api_key and not config.use_offline_demo:
            raw_payload = self._llm_review(document, report, client=client, config=config)
            notes.extend(_extract_critic_notes(raw_payload))
        return CriticResult(
            passed=not report.badcases,
            report=report,
            critic_notes=notes,
            raw_critic_payload=raw_payload,
        )

    def _llm_review(
        self,
        document: ScriptDocument,
        report: QualityReport,
        *,
        client: OpenAICompatibleJSONClient,
        config: LLMConfig,
    ) -> dict:
        payload = {
            "task": "review_short_drama_yaml",
            "review_rules": [
                "黄金三秒失败则指出应提前哪句原文冲突。",
                "video_prompt 含抽象文学词则给出摄影机可捕捉改法。",
                "结尾没有骗氪钩子则给出三种 cliffhanger 改法。",
                "只输出 JSON，包含 passed, badcases, root_causes, repair_suggestions。",
            ],
            "current_rule_report": report.model_dump(mode="json", exclude_none=True),
            "script": document.model_dump(mode="json", exclude_none=True),
        }
        prompt = json.dumps(payload, ensure_ascii=False, indent=2)
        return client._chat_json(  # noqa: SLF001 - internal adapter keeps one JSON client path
            f"{CRITIC_SYSTEM_PROMPT}\n\n{prompt}",
            config=config,
        )


def _extract_critic_notes(payload: dict | None) -> list[str]:
    if not payload:
        return []
    notes: list[str] = []
    for key in ["repair_suggestions", "root_causes", "badcases"]:
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    notes.append(item)
                elif isinstance(item, dict):
                    for inner_key in ["repair_suggestion", "reason", "root_cause"]:
                        inner = item.get(inner_key)
                        if isinstance(inner, str):
                            notes.append(inner)
    return notes
