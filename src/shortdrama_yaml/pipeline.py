from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pydantic import ValidationError

from .chapter_parser import Chapter, split_chapters, validate_minimum_chapters
from .evaluator import evaluate_document
from .iteration import run_critic_generator_loop
from .llm_client import LLMConfig, LLMGenerationError, OpenAICompatibleJSONClient
from .schema import QualityReport, ScriptDocument
from .scratchpad import apply_visual_bible, inject_visual_traits_into_prompts
from .yaml_io import document_to_yaml

ProgressCallback = Callable[[str, float], None]


@dataclass(frozen=True)
class ConversionOptions:
    title: str = "未命名网文短剧改编"
    genre: str = "都市逆袭"
    tone: str = "强冲突、快节奏、爽感反转"
    target_style: str = "竖屏短剧，黄金三秒强冲突，结尾钩子"
    shots_per_episode: int = 10
    llm_config: LLMConfig = LLMConfig()
    enable_scratchpad: bool = False
    enable_critic_loop: bool = False
    max_critic_rounds: int = 2
    use_llm_critic: bool = False


@dataclass(frozen=True)
class ConversionResult:
    chapters: list[Chapter]
    document: ScriptDocument
    yaml_text: str
    warnings: list[str]


def convert_novel_text(
    text: str,
    *,
    options: ConversionOptions,
    client: OpenAICompatibleJSONClient | None = None,
    progress_callback: ProgressCallback | None = None,
) -> ConversionResult:
    client = client or OpenAICompatibleJSONClient()
    warnings: list[str] = []

    _progress(progress_callback, "章节解析：识别章节边界", 0.12)
    parse_result = split_chapters(text)
    chapters = parse_result.chapters
    warnings.extend(parse_result.warnings)
    validate_minimum_chapters(chapters)

    _progress(progress_callback, "剧情抽取：准备角色/场景/冲突输入", 0.28)
    payload = client.generate_payload(
        chapters,
        title=options.title,
        genre=options.genre,
        tone=options.tone,
        target_style=options.target_style,
        shots_per_episode=options.shots_per_episode,
        config=options.llm_config,
    )

    _progress(progress_callback, "短剧改编：校验分集、钩子和镜头密度", 0.62)
    document = _validate_or_repair(payload, client=client, config=options.llm_config)

    _progress(progress_callback, "全局黑板：固定角色视觉资产", 0.7)
    if options.enable_scratchpad:
        document = apply_visual_bible(document)
        document = inject_visual_traits_into_prompts(document)

    _progress(progress_callback, "质量评估：检查网感、钩子、视觉可执行性", 0.78)
    structural_warnings = _quality_warnings(document, len(chapters))
    warnings.extend(structural_warnings)
    if options.enable_critic_loop:
        iteration = run_critic_generator_loop(
            document,
            input_chapter_count=len(chapters),
            structural_warnings=warnings,
            max_rounds=options.max_critic_rounds,
            client=client,
            config=options.llm_config,
            use_llm_critic=options.use_llm_critic,
        )
        document = iteration.document
        warnings = document.quality_report.warnings if document.quality_report else warnings
    else:
        quality_report = evaluate_document(
            document,
            input_chapter_count=len(chapters),
            structural_warnings=warnings,
            visual_bible=document.visual_bible,
        )
        document = document.model_copy(update={"quality_report": quality_report})
        warnings = quality_report.warnings

    _progress(progress_callback, "校验导出：生成可编辑 YAML", 0.92)
    yaml_text = document_to_yaml(document)
    _progress(progress_callback, "完成", 1.0)
    return ConversionResult(
        chapters=chapters,
        document=document,
        yaml_text=yaml_text,
        warnings=warnings,
    )


def _validate_or_repair(
    payload: dict,
    *,
    client: OpenAICompatibleJSONClient,
    config: LLMConfig,
) -> ScriptDocument:
    try:
        return ScriptDocument.model_validate(payload)
    except ValidationError as exc:
        if config.use_offline_demo or not config.api_key:
            raise
        try:
            repaired = client.repair_payload(payload, str(exc), config=config)
            return ScriptDocument.model_validate(repaired)
        except (LLMGenerationError, ValidationError) as repair_exc:
            raise ValueError(
                "模型输出未通过 Schema 校验，且自动修复失败。"
                f"\n原始校验错误：{exc}\n修复错误：{repair_exc}"
            ) from repair_exc


def _quality_warnings(document: ScriptDocument, input_chapter_count: int) -> list[str]:
    warnings: list[str] = []
    if input_chapter_count < 3:
        warnings.append("输入章节数少于 3，不满足题目要求。")
    if len(document.episodes) < input_chapter_count:
        warnings.append("输出集数少于输入章节数；若做了合并，请在答辩中说明合并策略。")
    for episode in document.episodes:
        if len(episode.shots) < 10 or len(episode.shots) > 15:
            warnings.append(f"{episode.episode_title} 镜头数不是 10-15。")
        if not episode.hook_summary:
            warnings.append(f"{episode.episode_title} 缺少 hook_summary。")
        if not episode.cliffhanger:
            warnings.append(f"{episode.episode_title} 缺少 cliffhanger。")
    if not document.source_map:
        warnings.append("缺少 source_map，无法证明改编来源。")
    return warnings


def _progress(callback: ProgressCallback | None, label: str, value: float) -> None:
    if callback:
        callback(label, value)
