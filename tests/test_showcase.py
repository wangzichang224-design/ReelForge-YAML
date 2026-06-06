from __future__ import annotations

from pathlib import Path

from shortdrama_yaml.showcase import build_showcase_episode, render_job_demo_script
from shortdrama_yaml.yaml_io import yaml_to_document


SAMPLE_YAML = Path("samples/deepseek_shadow_contract_3ch_optimized.yaml").read_text(encoding="utf-8")


def test_build_showcase_episode_exposes_video_ready_shot_cards() -> None:
    document = yaml_to_document(SAMPLE_YAML)
    showcase = build_showcase_episode(document, episode_number=1)

    assert showcase.episode_number == 1
    assert len(showcase.shots) == len(document.episodes[0].shots)
    first = showcase.shots[0]
    assert first.shot_id
    assert first.purpose
    assert first.subtitle
    assert first.visual_notes
    assert first.video_prompt
    assert first.source_excerpt
    assert first.source_chapter


def test_render_job_demo_script_matches_product_manager_jd_keywords() -> None:
    document = yaml_to_document(SAMPLE_YAML)
    script = render_job_demo_script(document)

    for keyword in ["需求分析", "产品设计", "架构选型", "代码实现", "复盘沉淀"]:
        assert keyword in script
    assert "不是只接收指令" in script
    assert "0 到 1" in script
