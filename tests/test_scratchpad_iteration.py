from __future__ import annotations

from pathlib import Path

from shortdrama_yaml.evaluator import evaluate_document
from shortdrama_yaml.iteration import run_critic_generator_loop
from shortdrama_yaml.llm_client import LLMConfig
from shortdrama_yaml.pipeline import ConversionOptions, convert_novel_text
from shortdrama_yaml.scratchpad import apply_visual_bible
from shortdrama_yaml.yaml_io import yaml_to_document


def test_visual_bible_adds_genre_specific_defaults() -> None:
    text = Path("samples/eval_novel_palace_lantern_3ch.txt").read_text(encoding="utf-8")
    result = convert_novel_text(
        text,
        options=ConversionOptions(
            title="长安灯影案",
            genre="古风权谋 / 证据反转",
            tone="强冲突",
            llm_config=LLMConfig(use_offline_demo=True),
            enable_scratchpad=True,
        ),
    )
    bible = result.document.visual_bible
    assert bible is not None
    assert "宫灯宴" in bible.key_locations
    assert "宫灯" in bible.key_props
    assert all("ancient costume" not in asset.negative_drift_terms for asset in bible.characters)


def test_critic_loop_rewrites_weak_visual_prompt_with_scene_hint() -> None:
    document = yaml_to_document(Path("samples/deepseek_shadow_contract_3ch_output.yaml").read_text(encoding="utf-8"))
    document = apply_visual_bible(document)
    data = document.model_dump(mode="json", exclude_none=True)
    data["episodes"][0]["shots"][2]["visual_track"]["video_prompt"] = (
        "A man shows complex emotion and inner thought, heartbroken, vertical 9:16"
    )
    edited = document.__class__.model_validate(data)
    before = evaluate_document(edited, input_chapter_count=3, visual_bible=edited.visual_bible)
    assert any(
        "episodes[0].shots[2]" in badcase.target_path and badcase.metric == "visual_executability"
        for badcase in before.badcases
    )

    result = run_critic_generator_loop(edited, input_chapter_count=3, max_rounds=2)
    repaired_prompt = result.document.episodes[0].shots[2].visual_track.video_prompt.lower()
    after = result.document.quality_report
    assert "scene interior" in repaired_prompt or "modern short drama interior" in repaired_prompt
    assert after is not None
    assert not [
        badcase
        for badcase in after.badcases
        if "episodes[0].shots[2]" in badcase.target_path and badcase.metric == "visual_executability"
    ]
