from __future__ import annotations

import re

from .schema import ScriptDocument, VisualAsset, VisualBible


DEFAULT_NEGATIVE_DRIFT_TERMS = [
    "red dress",
    "white shirt",
    "school uniform",
    "ancient costume",
    "teenage",
    "old man",
    "old woman",
]


def build_visual_bible(document: ScriptDocument) -> VisualBible:
    genre = document.series_metadata.genre
    tone = document.series_metadata.tone
    style = f"{genre}，{tone}，9:16 竖屏短剧，写实现代商业影像风格"
    defaults = _style_defaults(f"{genre} {tone}")
    key_locations = _merge_unique(defaults["locations"], _extract_locations(document))
    key_props = _merge_unique(defaults["props"], _extract_props(document))
    assets = [
        VisualAsset(
            character_id=character.character_id,
            name=character.name,
            locked_traits=_extract_locked_traits(character.visual_consistency_prompt),
            wardrobe=_extract_wardrobe(character.visual_consistency_prompt),
            visual_prompt=character.visual_consistency_prompt,
            negative_drift_terms=_negative_drift_terms(f"{genre} {tone}"),
        )
        for character in document.characters
    ]
    return VisualBible(
        global_style=style,
        palette=defaults["palette"],
        key_locations=key_locations,
        key_props=key_props,
        characters=assets,
    )


def apply_visual_bible(document: ScriptDocument, visual_bible: VisualBible | None = None) -> ScriptDocument:
    bible = visual_bible or build_visual_bible(document)
    return document.model_copy(update={"visual_bible": bible})


def inject_visual_traits_into_prompts(document: ScriptDocument) -> ScriptDocument:
    if not document.visual_bible:
        return document
    assets = {asset.character_id: asset for asset in document.visual_bible.characters}
    episodes = []
    for episode in document.episodes:
        shots = []
        for shot in episode.shots:
            prompt = shot.visual_track.video_prompt
            additions = []
            for character_id in shot.characters:
                asset = assets.get(character_id)
                if not asset:
                    continue
                trait = asset.locked_traits[0] if asset.locked_traits else asset.name
                if trait.lower() not in prompt.lower():
                    additions.append(asset.visual_prompt)
            if additions:
                visual_track = shot.visual_track.model_copy(
                    update={
                        "video_prompt": _append_prompt(prompt, additions),
                    }
                )
                shot = shot.model_copy(update={"visual_track": visual_track})
            shots.append(shot)
        episodes.append(episode.model_copy(update={"shots": shots}))
    return document.model_copy(update={"episodes": episodes})


def _extract_locked_traits(prompt: str) -> list[str]:
    parts = [
        part.strip(" .")
        for part in re.split(r",|，", prompt)
        if part.strip()
    ]
    useful = [
        part
        for part in parts
        if any(
            token in part.lower()
            for token in [
                "chinese",
                "woman",
                "man",
                "suit",
                "dress",
                "hair",
                "eyes",
                "jacket",
                "features",
                "presence",
            ]
        )
    ]
    return useful[:5] or parts[:3] or [prompt[:80]]


def _extract_wardrobe(prompt: str) -> str:
    for part in re.split(r",|，", prompt):
        if any(token in part.lower() for token in ["suit", "dress", "jacket", "shirt", "coat"]):
            return part.strip()
    return ""


def _extract_locations(document: ScriptDocument) -> list[str]:
    locations: set[str] = set()
    location_terms = ["会议室", "金融街", "地下车库", "顶楼", "宴会", "雨夜", "玻璃门", "办公室"]
    for episode in document.episodes:
        for shot in episode.shots:
            text = " ".join(
                [
                    shot.visual_track.visual_notes_zh,
                    shot.visual_track.video_prompt,
                    shot.source_ref.source_excerpt,
                ]
            )
            for term in location_terms:
                if term in text:
                    locations.add(term)
    return sorted(locations)


def _extract_props(document: ScriptDocument) -> list[str]:
    props: set[str] = set()
    prop_terms = ["文件袋", "支票", "U 盘", "U盘", "手机", "投影屏", "黑卡", "咖啡杯", "花束"]
    for episode in document.episodes:
        for shot in episode.shots:
            text = " ".join(
                [
                    shot.visual_track.visual_notes_zh,
                    shot.visual_track.video_prompt,
                    shot.source_ref.source_excerpt,
                ]
            )
            for term in prop_terms:
                if term in text:
                    props.add(term)
    return sorted(props)


def _style_defaults(style_text: str) -> dict[str, list[str]]:
    lowered = style_text.lower()
    if any(term in lowered for term in ["古风", "宫", "权谋", "长安", "palace", "ancient"]):
        return {
            "palette": ["warm lantern gold", "imperial red", "ink black", "cold moonlight"],
            "locations": ["宫灯宴", "午门", "掖庭", "军械库", "宫墙"],
            "props": ["宫灯", "灯芯", "玉印", "军械库暗账", "认罪书"],
        }
    if any(term in lowered for term in ["医疗", "病房", "遗嘱", "hospital", "will"]):
        return {
            "palette": ["clinical white", "monitor green", "cold blue", "warning red"],
            "locations": ["VIP 病房", "抢救室外", "护士站", "董事会视频会议"],
            "props": ["录音笔", "病历夹", "针管", "药品登记平板", "遗嘱"],
        }
    if any(term in lowered for term in ["职场", "客服", "退款", "office", "refund", "warehouse"]):
        return {
            "palette": ["fluorescent white", "screen blue", "rainy glass gray", "warning red"],
            "locations": ["客服工位", "会议室", "便利店监控屏", "仓库 7 号门"],
            "props": ["退款单", "录屏文件", "耳机缓存", "监控回放", "审计日志"],
        }
    return {
        "palette": ["deep charcoal", "cold cyan", "warm amber", "rainy glass reflections"],
        "locations": [],
        "props": [],
    }


def _negative_drift_terms(style_text: str) -> list[str]:
    terms = list(DEFAULT_NEGATIVE_DRIFT_TERMS)
    lowered = style_text.lower()
    if any(term in lowered for term in ["古风", "宫", "权谋", "长安", "palace", "ancient"]):
        terms = [term for term in terms if term != "ancient costume"]
    return terms


def _merge_unique(first: list[str], second: list[str]) -> list[str]:
    output: list[str] = []
    for item in [*first, *second]:
        if item and item not in output:
            output.append(item)
    return output


def _append_prompt(prompt: str, additions: list[str]) -> str:
    unique: list[str] = []
    seen: set[str] = set()
    for addition in additions:
        normalized = addition.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    if not unique:
        return prompt
    return f"{prompt.rstrip(' .')}. Character consistency: {'; '.join(unique)}."
