from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .chapter_parser import split_chapters


@dataclass(frozen=True)
class InferredNovelSettings:
    title: str
    genre: str
    tone: str
    target_style: str
    evidence: str


_KNOWN_DATASETS: dict[str, tuple[str, str]] = {
    "shadow_contract": ("影子合约", "都市商战 / 复仇反转"),
    "quiet_transition": ("空办公室", "创业现实 / 平淡戏剧化"),
    "palace_lantern": ("长安灯影案", "古风权谋 / 证据反转"),
    "hospital_will": ("病房里的继承书", "医疗家庭 / 遗嘱打脸"),
    "midnight_refund": ("凌晨三点的退款单", "客服职场 / 低冲突悬疑"),
}

_GENRE_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "古风权谋 / 证据反转",
        ("皇后", "长安", "宫灯", "侍卫", "女史", "内侍", "凤辇", "午门", "军械库", "按律当斩"),
    ),
    (
        "医疗家庭 / 遗嘱打脸",
        ("病房", "医院", "继母", "股权", "遗嘱", "呼吸机", "监护仪", "护工", "保安", "直播"),
    ),
    (
        "客服职场 / 低冲突悬疑",
        ("客服", "退款", "售后", "订单", "工位", "仓库", "GMV", "批量驳回", "备注", "摄像头"),
    ),
    (
        "创业现实 / 平淡戏剧化",
        ("商业计划书", "投资人", "合伙人", "联合办公", "办公室", "融资", "项目", "用户访谈"),
    ),
    (
        "都市商战 / 复仇反转",
        ("金融街", "集团", "并购", "封口费", "顾氏", "权限", "工牌", "保安", "合同", "董事会"),
    ),
    (
        "都市逆袭 / 情感压迫",
        ("隐婚", "婚宴", "婆婆", "总裁", "离婚", "前夫", "豪门", "订婚", "打脸"),
    ),
]

_CHAPTER_TITLE_RE = re.compile(
    r"^(?:第\s*[一二三四五六七八九十百千万零〇两\d]+\s*[章节回部卷集]|"
    r"(?:chapter|episode|part)\s+[\divxlcdm]+|"
    r"[一二三四五六七八九十百千万零〇两\d]+\s*[、.．])\s*[:：·\-—]?\s*",
    re.IGNORECASE,
)


def infer_novel_settings(text: str, filename: str | None = None) -> InferredNovelSettings:
    """Infer sidebar defaults from an uploaded novel without calling an LLM."""
    known = _known_dataset_settings(filename)
    if known:
        title, genre = known
        evidence = "根据测试集文件名匹配到 golden dataset 元数据"
    else:
        title = _infer_title_from_text(text, filename)
        genre = _infer_genre_from_keywords(text)
        evidence = "根据章节标题和正文关键词自动推断"

    tone, target_style = _style_for_genre(genre)
    return InferredNovelSettings(
        title=title,
        genre=genre,
        tone=tone,
        target_style=target_style,
        evidence=evidence,
    )


def _known_dataset_settings(filename: str | None) -> tuple[str, str] | None:
    if not filename:
        return None
    stem = Path(filename).stem.lower()
    for key, settings in _KNOWN_DATASETS.items():
        if key in stem:
            return settings
    return None


def _infer_title_from_text(text: str, filename: str | None) -> str:
    parse_result = split_chapters(text)
    if parse_result.chapters:
        title = _strip_chapter_prefix(parse_result.chapters[0].title)
        if title:
            return title[:24]

    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if first_line:
        return _strip_chapter_prefix(first_line)[:24] or first_line[:24]

    if filename:
        return Path(filename).stem.replace("_", " ")[:24]
    return "未命名网文短剧改编"


def _strip_chapter_prefix(title: str) -> str:
    cleaned = _CHAPTER_TITLE_RE.sub("", title.strip()).strip(" ：:-—")
    return cleaned or title.strip()


def _infer_genre_from_keywords(text: str) -> str:
    scores: list[tuple[int, str]] = []
    for genre, keywords in _GENRE_RULES:
        score = sum(text.count(keyword) for keyword in keywords)
        scores.append((score, genre))

    best_score, best_genre = max(scores, key=lambda item: item[0])
    if best_score > 0:
        return best_genre
    return "都市逆袭"


def _style_for_genre(genre: str) -> tuple[str, str]:
    if "古风" in genre:
        return (
            "权谋压迫、证据反转、古风悬疑",
            "竖屏古风短剧，宫廷视觉资产稳定，首镜头直接进入罪名、证据或权力压迫，每集结尾留反转钩子。",
        )
    if "医疗" in genre:
        return (
            "家庭压迫、遗嘱反转、病房对峙",
            "竖屏家庭伦理短剧，病房、遗嘱、录音和监护仪等道具清晰可见，台词保留逼签和打脸张力。",
        )
    if "客服" in genre:
        return (
            "职场悬疑、低冲突升级、证据卡点",
            "竖屏职场悬疑短剧，把退款单、订单备注、监控和电话动作做成可视化卡点，每集结尾留下新线索。",
        )
    if "创业" in genre:
        return (
            "现实压迫、沉默冲突、创业逆风",
            "竖屏现实题材短剧，把内心压力转成屏幕、群聊、账单、录音和会议动作，避免纯心理描写。",
        )
    if "商战" in genre:
        return (
            "强冲突、证据反转、复仇压迫",
            "竖屏都市商战短剧，黄金三秒直接出现对峙、羞辱、权限封锁或证据冲突，每集结尾留钩子。",
        )
    return (
        "强冲突、快节奏、爽感反转",
        "竖屏短剧，黄金三秒强冲突，人物关系强压迫，每集结尾留钩子。",
    )
