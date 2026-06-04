from __future__ import annotations

from pathlib import Path

import yaml

from shortdrama_yaml.llm_client import LLMConfig
from shortdrama_yaml.pipeline import ConversionOptions, convert_novel_text
from shortdrama_yaml.yaml_io import yaml_to_document


SAMPLE_TEXT = Path("samples/sample_novel_three_chapters.txt").read_text(encoding="utf-8")


def test_offline_pipeline_generates_valid_yaml() -> None:
    result = convert_novel_text(
        SAMPLE_TEXT,
        options=ConversionOptions(
            title="隐婚风暴",
            genre="都市逆袭",
            tone="强冲突、快节奏、爽感反转",
            shots_per_episode=10,
            llm_config=LLMConfig(use_offline_demo=True),
        ),
    )

    loaded = yaml.safe_load(result.yaml_text)
    assert isinstance(loaded, dict)
    document = yaml_to_document(result.yaml_text)
    assert len(document.episodes) == 3
    assert document.quality_report is not None
    assert document.quality_report.schema_valid is True


def test_quality_constraints_are_visible() -> None:
    result = convert_novel_text(
        SAMPLE_TEXT,
        options=ConversionOptions(shots_per_episode=10, llm_config=LLMConfig(use_offline_demo=True)),
    )
    document = result.document
    assert all(10 <= len(episode.shots) <= 15 for episode in document.episodes)
    assert all(episode.shots[0].purpose == "opening_hook" for episode in document.episodes)
    assert all(episode.shots[-1].purpose == "cliffhanger" for episode in document.episodes)
    assert all(
        "9:16" in shot.visual_track.video_prompt
        for episode in document.episodes
        for shot in episode.shots
    )
    assert len(document.source_map) >= len(document.episodes)
