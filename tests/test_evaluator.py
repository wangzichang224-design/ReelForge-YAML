from __future__ import annotations

from pathlib import Path

from shortdrama_yaml.evaluator import evaluate_document
from shortdrama_yaml.iteration import run_critic_generator_loop
from shortdrama_yaml.schema import ScriptDocument
from shortdrama_yaml.scratchpad import apply_visual_bible, inject_visual_traits_into_prompts
from shortdrama_yaml.yaml_io import yaml_to_document


DEEPSEEK_SAMPLE = Path("samples/deepseek_shadow_contract_3ch_output.yaml")
OPTIMIZED_SAMPLE = Path("samples/deepseek_shadow_contract_3ch_optimized.yaml")


def test_deepseek_sample_exposes_opening_hook_badcases() -> None:
    document = yaml_to_document(DEEPSEEK_SAMPLE.read_text(encoding="utf-8"))
    report = evaluate_document(document, input_chapter_count=3)
    hook_badcases = [badcase for badcase in report.badcases if badcase.metric == "hook"]
    assert len(hook_badcases) == 3
    assert report.episode_scores[0].hook_score < 0.75


def test_critic_loop_repairs_opening_hook_badcases() -> None:
    document = yaml_to_document(DEEPSEEK_SAMPLE.read_text(encoding="utf-8"))
    document = apply_visual_bible(document)
    result = run_critic_generator_loop(
        document,
        input_chapter_count=3,
        max_rounds=2,
    )
    repaired = result.document
    assert len(repaired.episodes) == 3
    assert sum(len(episode.shots) for episode in repaired.episodes) == 30
    assert repaired.quality_report is not None
    assert all(score.hook_score >= 0.75 for score in repaired.quality_report.episode_scores)
    assert all(score.cliffhanger_score >= 0.75 for score in repaired.quality_report.episode_scores)
    assert all(score.power_shift_score >= 0.75 for score in repaired.quality_report.episode_scores)


def test_checked_in_optimized_sample_keeps_core_scores_passing() -> None:
    document = yaml_to_document(OPTIMIZED_SAMPLE.read_text(encoding="utf-8"))
    report = evaluate_document(document, input_chapter_count=3, visual_bible=document.visual_bible)
    assert len(document.episodes) == 3
    assert sum(len(episode.shots) for episode in document.episodes) == 30
    assert all(score.hook_score >= 0.75 for score in report.episode_scores)
    assert all(score.cliffhanger_score >= 0.75 for score in report.episode_scores)
    assert all(score.power_shift_score >= 0.75 for score in report.episode_scores)
    assert all(score.visual_executability_score >= 0.75 for score in report.episode_scores)
    assert all(score.continuity_score >= 0.75 for score in report.episode_scores)


def test_visual_executability_rejects_abstract_prompt() -> None:
    document = yaml_to_document(DEEPSEEK_SAMPLE.read_text(encoding="utf-8"))
    data = document.model_dump(mode="json", exclude_none=True)
    data["episodes"][0]["shots"][0]["visual_track"]["video_prompt"] = (
        "A man shows complex emotion and inner thought, heartbroken, vertical 9:16"
    )
    edited = ScriptDocument.model_validate(data)
    report = evaluate_document(edited, input_chapter_count=3)
    assert any(badcase.metric == "visual_executability" for badcase in report.badcases)


def test_dialogue_language_rejects_non_chinese_dialogue() -> None:
    document = yaml_to_document(DEEPSEEK_SAMPLE.read_text(encoding="utf-8"))
    data = document.model_dump(mode="json", exclude_none=True)
    for shot in data["episodes"][0]["shots"]:
        for line in shot["audio_track"]["dialogue"]:
            line["text"] = "I will expose the truth now."
    edited = ScriptDocument.model_validate(data)
    report = evaluate_document(edited, input_chapter_count=3)
    assert report.episode_scores[0].dialogue_language_score < 0.75
    assert any(badcase.metric == "dialogue_language" for badcase in report.badcases)


def test_ancient_costume_is_allowed_for_palace_visual_bible() -> None:
    document = yaml_to_document(DEEPSEEK_SAMPLE.read_text(encoding="utf-8"))
    document = apply_visual_bible(document)
    assert document.visual_bible is not None

    bible_data = document.visual_bible.model_dump(mode="json")
    bible_data["global_style"] = "古风权谋，长安宫廷，palace intrigue, ancient costume visual style"
    bible_data["characters"][0]["negative_drift_terms"] = ["ancient costume"]

    data = document.model_dump(mode="json", exclude_none=True)
    data["visual_bible"] = bible_data
    first_character_id = data["visual_bible"]["characters"][0]["character_id"]
    locked_trait = data["visual_bible"]["characters"][0]["locked_traits"][0]
    for shot in data["episodes"][0]["shots"]:
        shot["characters"] = [first_character_id]
        shot["visual_track"]["video_prompt"] = (
            f"Close-up shot, the character is standing in ancient costume, holding evidence in palace interior, "
            f"cinematic lighting, vertical 9:16. Character consistency: {locked_trait}."
        )
    edited = ScriptDocument.model_validate(data)
    report = evaluate_document(edited, input_chapter_count=3, visual_bible=edited.visual_bible)
    assert not [
        badcase
        for badcase in report.badcases
        if badcase.metric == "continuity" and "episodes[0]" in badcase.target_path
    ]


def test_power_shift_fails_without_reversal_or_payoff() -> None:
    document = yaml_to_document(DEEPSEEK_SAMPLE.read_text(encoding="utf-8"))
    data = document.model_dump(mode="json", exclude_none=True)
    for shot in data["episodes"][0]["shots"]:
        if shot["purpose"] in {"reversal", "payoff"}:
            shot["purpose"] = "emotional_pressure"
    data["episodes"][0]["shots"][0]["purpose"] = "opening_hook"
    data["episodes"][0]["shots"][-1]["purpose"] = "cliffhanger"
    data["episodes"][0]["emotional_curve"] = ["压抑", "沉默", "等待"]
    edited = ScriptDocument.model_validate(data)
    report = evaluate_document(edited, input_chapter_count=3)
    assert report.episode_scores[0].power_shift_score < 0.75
    assert any(badcase.metric == "power_shift" for badcase in report.badcases)


def test_continuity_fails_when_visual_bible_is_not_inherited() -> None:
    document = yaml_to_document(DEEPSEEK_SAMPLE.read_text(encoding="utf-8"))
    document = apply_visual_bible(document)
    report = evaluate_document(document, input_chapter_count=3, visual_bible=document.visual_bible)
    assert any(badcase.metric == "continuity" for badcase in report.badcases)


def test_continuity_passes_after_trait_injection() -> None:
    document = yaml_to_document(DEEPSEEK_SAMPLE.read_text(encoding="utf-8"))
    document = apply_visual_bible(document)
    document = inject_visual_traits_into_prompts(document)
    report = evaluate_document(document, input_chapter_count=3, visual_bible=document.visual_bible)
    assert all(score.continuity_score >= 0.75 for score in report.episode_scores)
