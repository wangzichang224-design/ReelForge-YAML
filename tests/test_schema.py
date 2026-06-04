from __future__ import annotations

import pytest
from pydantic import ValidationError

from shortdrama_yaml.llm_client import robust_json_loads
from shortdrama_yaml.offline_generator import build_offline_script
from shortdrama_yaml.schema import ScriptDocument
from shortdrama_yaml.chapter_parser import Chapter


def test_schema_rejects_non_english_video_prompt() -> None:
    payload = build_offline_script(
        [
            Chapter("ch001", "第一章", "他被羞辱。"),
            Chapter("ch002", "第二章", "黑卡出现。"),
            Chapter("ch003", "第三章", "真相反咬。"),
        ],
        title="测试",
        genre="都市",
        tone="爽感",
        shots_per_episode=10,
    )
    payload["episodes"][0]["shots"][0]["visual_track"]["video_prompt"] = "这是一个中文提示词，没有英文视频模型描述。"
    with pytest.raises(ValidationError):
        ScriptDocument.model_validate(payload)


def test_robust_json_loads_strips_fenced_block() -> None:
    parsed = robust_json_loads('```json\n{"a": 1}\n```')
    assert parsed == {"a": 1}
