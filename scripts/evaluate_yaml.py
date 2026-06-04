from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from shortdrama_yaml.evaluator import evaluate_document
from shortdrama_yaml.iteration import run_critic_generator_loop
from shortdrama_yaml.scratchpad import apply_visual_bible
from shortdrama_yaml.yaml_io import document_to_yaml, yaml_to_document


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate or locally optimize a ReelForge YAML script.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="")
    parser.add_argument("--optimize", action="store_true")
    parser.add_argument("--scratchpad", action="store_true")
    parser.add_argument("--max-rounds", type=int, default=2)
    args = parser.parse_args()

    input_path = PROJECT_ROOT / args.input
    document = yaml_to_document(input_path.read_text(encoding="utf-8"))
    if args.scratchpad:
        document = apply_visual_bible(document)

    if args.optimize:
        result = run_critic_generator_loop(
            document,
            input_chapter_count=document.quality_report.input_chapter_count if document.quality_report else len(document.episodes),
            max_rounds=args.max_rounds,
        )
        document = result.document
        report = result.critic_result.report
    else:
        report = evaluate_document(
            document,
            input_chapter_count=document.quality_report.input_chapter_count if document.quality_report else len(document.episodes),
            visual_bible=document.visual_bible,
        )
        document = document.model_copy(update={"quality_report": report})

    if args.output:
        output_path = PROJECT_ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(document_to_yaml(document), encoding="utf-8")
        print(f"output={output_path}")

    print(f"input_chapters={report.input_chapter_count}")
    print(f"schema_valid={report.schema_valid}")
    print(f"overall_score={report.overall_score}")
    print(f"episodes={report.total_episodes}")
    print(f"shots={report.total_shots}")
    print(f"badcases={len(report.badcases)}")
    for score in report.episode_scores:
        print(
            "EP{episode}: hook={hook:.2f} cliff={cliff:.2f} power={power:.2f} visual={visual:.2f} continuity={continuity:.2f} pass={passed}".format(
                episode=score.episode_number,
                hook=score.hook_score,
                cliff=score.cliffhanger_score,
                power=score.power_shift_score,
                visual=score.visual_executability_score,
                continuity=score.continuity_score,
                passed=score.passed,
            )
        )


if __name__ == "__main__":
    main()
