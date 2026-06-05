from __future__ import annotations

from pathlib import Path

import yaml

from shortdrama_yaml.chapter_parser import split_chapters


GOLDEN_DATASET = Path("samples/golden_dataset.yaml")
NEW_DATASET_IDS = {"palace_lantern", "hospital_will", "midnight_refund"}


def test_new_golden_dataset_entries_have_three_chapters() -> None:
    data = yaml.safe_load(GOLDEN_DATASET.read_text(encoding="utf-8"))
    entries = {
        entry["id"]: entry
        for entry in data["datasets"]
        if entry["id"] in NEW_DATASET_IDS
    }
    assert set(entries) == NEW_DATASET_IDS

    for entry in entries.values():
        sample_path = Path(entry["input"])
        assert sample_path.exists()
        result = split_chapters(sample_path.read_text(encoding="utf-8"))
        assert len(result.chapters) == entry["target"]["expected_chapters"]
        assert not result.warnings
