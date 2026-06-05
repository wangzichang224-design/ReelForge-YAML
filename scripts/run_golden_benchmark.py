from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from shortdrama_yaml.chapter_parser import split_chapters, validate_minimum_chapters
from shortdrama_yaml.llm_client import LLMConfig
from shortdrama_yaml.pipeline import ConversionOptions, convert_novel_text
from shortdrama_yaml.schema import QualityReport


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ReelForge golden dataset benchmark.")
    parser.add_argument("--dataset", default="samples/golden_dataset.yaml")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--sample-id", default="")
    args = parser.parse_args()

    dataset_path = PROJECT_ROOT / args.dataset
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = yaml.safe_load(dataset_path.read_text(encoding="utf-8"))
    entries = dataset.get("datasets", [])
    if args.sample_id:
        entries = [entry for entry in entries if entry["id"] == args.sample_id]
    if not entries:
        raise ValueError(f"No golden dataset entries matched sample_id={args.sample_id!r}")

    results = [run_entry(entry) for entry in entries]
    summary = build_summary(results)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": args.dataset,
        "mode": "offline_demo_raw_vs_scratchpad_critic",
        "summary": summary,
        "results": results,
    }

    json_path = output_dir / "golden_benchmark.json"
    md_path = output_dir / "golden_benchmark.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")

    print(f"json={json_path}")
    print(f"markdown={md_path}")
    print(f"samples={summary['sample_count']}")
    print(f"raw_avg={summary['raw_average_score']}")
    print(f"optimized_avg={summary['optimized_average_score']}")
    print(f"badcase_reduction={summary['badcase_reduction_rate']}")


def run_entry(entry: dict[str, Any]) -> dict[str, Any]:
    input_path = PROJECT_ROOT / entry["input"]
    text = input_path.read_text(encoding="utf-8")
    parse_result = split_chapters(text)
    validate_minimum_chapters(parse_result.chapters)

    target = entry.get("target", {})
    expected_episodes = int(target.get("expected_episodes") or len(parse_result.chapters))
    expected_shots = int(target.get("expected_shots") or expected_episodes * 10)
    shots_per_episode = max(10, min(15, expected_shots // max(expected_episodes, 1)))
    genre = target.get("genre", "短剧评测样例")

    raw = convert_novel_text(
        text,
        options=ConversionOptions(
            title=entry["title"],
            genre=genre,
            tone="强冲突、快节奏、可评测短剧改编",
            shots_per_episode=shots_per_episode,
            llm_config=LLMConfig(use_offline_demo=True),
            enable_scratchpad=False,
            enable_critic_loop=False,
        ),
    )
    optimized = convert_novel_text(
        text,
        options=ConversionOptions(
            title=entry["title"],
            genre=genre,
            tone="强冲突、快节奏、可评测短剧改编",
            shots_per_episode=shots_per_episode,
            llm_config=LLMConfig(use_offline_demo=True),
            enable_scratchpad=True,
            enable_critic_loop=True,
            max_critic_rounds=2,
        ),
    )

    return {
        "id": entry["id"],
        "title": entry["title"],
        "genre": genre,
        "input": entry["input"],
        "chapter_count": len(parse_result.chapters),
        "expected_episodes": expected_episodes,
        "expected_shots": expected_shots,
        "raw": report_to_dict(raw.document.quality_report),
        "optimized": report_to_dict(optimized.document.quality_report),
        "target_must_have": target.get("must_have", []),
    }


def report_to_dict(report: QualityReport | None) -> dict[str, Any]:
    if report is None:
        return {"overall_score": 0, "badcase_count": 0, "episodes": 0, "shots": 0, "root_causes": []}
    return {
        "overall_score": report.overall_score,
        "badcase_count": len(report.badcases),
        "episodes": report.total_episodes,
        "shots": report.total_shots,
        "schema_valid": report.schema_valid,
        "root_causes": report.root_causes[:5],
        "episode_scores": [
            {
                "episode": score.episode_number,
                "hook": score.hook_score,
                "cliffhanger": score.cliffhanger_score,
                "power_shift": score.power_shift_score,
                "visual": score.visual_executability_score,
                "continuity": score.continuity_score,
                "passed": score.passed,
            }
            for score in report.episode_scores
        ],
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    raw_scores = [item["raw"]["overall_score"] or 0 for item in results]
    optimized_scores = [item["optimized"]["overall_score"] or 0 for item in results]
    raw_badcases = sum(item["raw"]["badcase_count"] for item in results)
    optimized_badcases = sum(item["optimized"]["badcase_count"] for item in results)
    reduction = 0.0 if raw_badcases == 0 else 1 - optimized_badcases / raw_badcases
    return {
        "sample_count": len(results),
        "raw_average_score": round(mean(raw_scores), 3) if raw_scores else 0.0,
        "optimized_average_score": round(mean(optimized_scores), 3) if optimized_scores else 0.0,
        "raw_badcases": raw_badcases,
        "optimized_badcases": optimized_badcases,
        "badcase_reduction_rate": round(reduction, 3),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Golden Benchmark Report",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Dataset: `{payload['dataset']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Samples: {summary['sample_count']}",
        f"- Raw average score: {summary['raw_average_score']}",
        f"- Optimized average score: {summary['optimized_average_score']}",
        f"- Raw badcases: {summary['raw_badcases']}",
        f"- Optimized badcases: {summary['optimized_badcases']}",
        f"- Badcase reduction rate: {summary['badcase_reduction_rate']}",
        "",
        "| Sample | Genre | Raw Score | Optimized Score | Raw Badcases | Optimized Badcases |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in payload["results"]:
        lines.append(
            "| {title} | {genre} | {raw_score} | {optimized_score} | {raw_badcases} | {optimized_badcases} |".format(
                title=item["title"],
                genre=item["genre"],
                raw_score=item["raw"]["overall_score"],
                optimized_score=item["optimized"]["overall_score"],
                raw_badcases=item["raw"]["badcase_count"],
                optimized_badcases=item["optimized"]["badcase_count"],
            )
        )
    lines.extend(["", "## Root Cause Snapshot", ""])
    for item in payload["results"]:
        raw_causes = "；".join(item["raw"].get("root_causes", [])) or "none"
        optimized_causes = "；".join(item["optimized"].get("root_causes", [])) or "none"
        lines.append(f"- **{item['title']} raw**: {raw_causes}")
        lines.append(f"- **{item['title']} optimized**: {optimized_causes}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
