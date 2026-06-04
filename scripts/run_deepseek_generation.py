from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from shortdrama_yaml.llm_client import LLMConfig
from shortdrama_yaml.pipeline import ConversionOptions, convert_novel_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ReelForge YAML generation with DeepSeek/OpenAI-compatible API."
    )
    parser.add_argument("--input", default="samples/eval_novel_shadow_contract.txt")
    parser.add_argument("--output", default="samples/deepseek_shadow_contract_output.yaml")
    parser.add_argument("--title", default="影子合约")
    parser.add_argument("--genre", default="都市商战 / 复仇反转")
    parser.add_argument("--tone", default="强冲突、证据反转、冷感商战、短剧钩子")
    parser.add_argument("--model", default=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    parser.add_argument("--base-url", default=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    parser.add_argument("--shots", type=int, default=10)
    parser.add_argument("--scratchpad", action="store_true")
    parser.add_argument("--critic-loop", action="store_true")
    args = parser.parse_args()

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("Missing DEEPSEEK_API_KEY environment variable.")

    input_path = PROJECT_ROOT / args.input
    output_path = PROJECT_ROOT / args.output
    text = input_path.read_text(encoding="utf-8")

    result = convert_novel_text(
        text,
        options=ConversionOptions(
            title=args.title,
            genre=args.genre,
            tone=args.tone,
            target_style="竖屏短剧，黄金三秒强冲突，证据链反转，每集末尾强 cliffhanger。",
            shots_per_episode=args.shots,
            llm_config=LLMConfig(
                api_key=api_key,
                base_url=args.base_url,
                model=args.model,
                temperature=0.2,
                max_tokens=16000,
                timeout_seconds=180,
                use_offline_demo=False,
            ),
            enable_scratchpad=args.scratchpad,
            enable_critic_loop=args.critic_loop,
        ),
    )
    output_path.write_text(result.yaml_text, encoding="utf-8")

    print(f"output={output_path}")
    print(f"chapters={len(result.chapters)}")
    print(f"episodes={len(result.document.episodes)}")
    print(f"shots={sum(len(episode.shots) for episode in result.document.episodes)}")
    print(f"warnings={len(result.warnings)}")


if __name__ == "__main__":
    main()
