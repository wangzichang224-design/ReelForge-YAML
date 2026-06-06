from __future__ import annotations

from pathlib import Path

from shortdrama_yaml.metadata_inference import infer_novel_settings


def test_known_golden_dataset_file_infers_exact_settings() -> None:
    text = Path("samples/eval_novel_palace_lantern_3ch.txt").read_text(encoding="utf-8")

    settings = infer_novel_settings(text, "eval_novel_palace_lantern_3ch.txt")

    assert settings.title == "长安灯影案"
    assert settings.genre == "古风权谋 / 证据反转"
    assert "古风" in settings.tone
    assert "宫廷" in settings.target_style


def test_unknown_file_infers_title_and_genre_from_content() -> None:
    text = Path("samples/eval_novel_hospital_will_3ch.txt").read_text(encoding="utf-8")

    settings = infer_novel_settings(text, "uploaded_story.txt")

    assert settings.title == "病房录音"
    assert settings.genre == "医疗家庭 / 遗嘱打脸"
    assert "病房" in settings.target_style
