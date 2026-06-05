from __future__ import annotations

import yaml

from scripts.run_golden_benchmark import build_summary, run_entry


def test_golden_benchmark_runs_single_entry() -> None:
    dataset = yaml.safe_load(open("samples/golden_dataset.yaml", encoding="utf-8"))
    entry = next(item for item in dataset["datasets"] if item["id"] == "palace_lantern")
    result = run_entry(entry)
    assert result["chapter_count"] == 3
    assert result["raw"]["episodes"] == 3
    assert result["raw"]["shots"] == 30
    assert result["optimized"]["episodes"] == 3
    assert result["optimized"]["shots"] == 30
    assert result["optimized"]["overall_score"] >= result["raw"]["overall_score"]


def test_golden_benchmark_summary_tracks_badcase_reduction() -> None:
    results = [
        {
            "raw": {"overall_score": 0.7, "badcase_count": 10},
            "optimized": {"overall_score": 0.9, "badcase_count": 4},
        },
        {
            "raw": {"overall_score": 0.8, "badcase_count": 5},
            "optimized": {"overall_score": 0.95, "badcase_count": 2},
        },
    ]
    summary = build_summary(results)
    assert summary["sample_count"] == 2
    assert summary["raw_average_score"] == 0.75
    assert summary["optimized_average_score"] == 0.925
    assert summary["badcase_reduction_rate"] == 0.6
