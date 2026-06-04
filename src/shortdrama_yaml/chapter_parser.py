from __future__ import annotations

import re
from dataclasses import dataclass


CHINESE_CHAPTER_RE = re.compile(
    r"^\s*((?:第\s*[一二三四五六七八九十百千万零〇两\d]+\s*[章节回部卷集][^\n]*)|(?:[一二三四五六七八九十百千万零〇两\d]+\s*[、.．]\s*[^\n]{1,40}))\s*$",
    re.MULTILINE,
)

ENGLISH_CHAPTER_RE = re.compile(
    r"^\s*((?:chapter|episode|part)\s+[\divxlcdm]+[^\n]*)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class Chapter:
    chapter_id: str
    title: str
    text: str


@dataclass(frozen=True)
class ChapterParseResult:
    chapters: list[Chapter]
    warnings: list[str]


def split_chapters(raw_text: str) -> ChapterParseResult:
    text = _normalize_text(raw_text)
    if not text:
        return ChapterParseResult(chapters=[], warnings=["输入文本为空。"])

    matches = sorted(
        list(CHINESE_CHAPTER_RE.finditer(text)) + list(ENGLISH_CHAPTER_RE.finditer(text)),
        key=lambda match: match.start(),
    )
    if len(matches) >= 2:
        chapters = _chapters_from_heading_matches(text, matches)
        warnings: list[str] = []
        if len(chapters) < 3:
            warnings.append("识别到章节标题，但章节数少于 3。")
        return ChapterParseResult(chapters=chapters, warnings=warnings)

    fallback = _fallback_paragraph_chunks(text)
    warnings = [
        "未稳定识别章节标题，已按长段落自动切分为章节草稿；建议补充“第1章/第2章/第3章”标题。"
    ]
    return ChapterParseResult(chapters=fallback, warnings=warnings)


def validate_minimum_chapters(chapters: list[Chapter], minimum: int = 3) -> None:
    if len(chapters) < minimum:
        raise ValueError(f"至少需要 {minimum} 个章节，当前只识别到 {len(chapters)} 个。")


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _chapters_from_heading_matches(text: str, matches: list[re.Match[str]]) -> list[Chapter]:
    chapters: list[Chapter] = []
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        content_start = match.end()
        content_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[content_start:content_end].strip()
        if not body:
            continue
        chapters.append(
            Chapter(
                chapter_id=f"ch{len(chapters) + 1:03d}",
                title=title,
                text=body,
            )
        )
    return chapters


def _fallback_paragraph_chunks(text: str) -> list[Chapter]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) >= 3:
        chunk_count = min(len(paragraphs), 3)
        chunks = _balanced_chunks(paragraphs, chunk_count)
        return [
            Chapter(chapter_id=f"ch{index + 1:03d}", title=f"自动切分章节 {index + 1}", text="\n\n".join(chunk))
            for index, chunk in enumerate(chunks)
        ]

    sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])", text) if s.strip()]
    chunk_count = 3 if len(sentences) >= 9 else max(1, min(3, len(sentences)))
    chunks = _balanced_chunks(sentences, chunk_count)
    return [
        Chapter(chapter_id=f"ch{index + 1:03d}", title=f"自动切分章节 {index + 1}", text="".join(chunk))
        for index, chunk in enumerate(chunks)
        if chunk
    ]


def _balanced_chunks(items: list[str], chunk_count: int) -> list[list[str]]:
    if chunk_count <= 0:
        return []
    chunk_size = max(1, (len(items) + chunk_count - 1) // chunk_count)
    chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
    if len(chunks) > chunk_count:
        chunks[chunk_count - 1].extend(item for chunk in chunks[chunk_count:] for item in chunk)
        chunks = chunks[:chunk_count]
    return chunks
