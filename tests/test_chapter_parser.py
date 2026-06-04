from __future__ import annotations

import pytest

from shortdrama_yaml.chapter_parser import split_chapters, validate_minimum_chapters


def test_split_chinese_chapters() -> None:
    text = """
第一章 开端
他走进大厅。冲突爆发。

第二章 反转
黑卡出现。众人震惊。

第三章 悬念
匿名短信出现。真相反咬。
"""
    result = split_chapters(text)
    assert len(result.chapters) == 3
    assert result.chapters[0].chapter_id == "ch001"
    assert "第一章" in result.chapters[0].title


def test_less_than_three_chapters_is_rejected() -> None:
    text = """
第一章 开端
他走进大厅。

第二章 反转
黑卡出现。
"""
    result = split_chapters(text)
    with pytest.raises(ValueError, match="至少需要 3 个章节"):
        validate_minimum_chapters(result.chapters)


def test_fallback_paragraph_chunks() -> None:
    text = """
第一段没有规范标题，但有足够内容。主角被当众羞辱，冲突出现。

第二段继续推进。反派逼问，女主动摇，主角隐忍。

第三段出现反转。证据曝光，所有人震惊，新的悬念出现。
"""
    result = split_chapters(text)
    assert len(result.chapters) == 3
    assert result.warnings
