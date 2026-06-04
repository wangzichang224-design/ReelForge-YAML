from __future__ import annotations

import re

from .chapter_parser import Chapter


DEFAULT_CHARACTERS = [
    {
        "character_id": "char_hero",
        "name": "沈砚",
        "role": "男主/被低估的关键人物",
        "relationship": "与女主存在误会，被反派当众羞辱",
        "motivation": "守住尊严，同时揭开隐藏身份和真相",
        "visual_consistency_prompt": "young Chinese man, 25 years old, sharp eyes, simple black jacket, restrained anger, photorealistic vertical drama style",
        "voice_profile": "低沉克制，爆发时语速加快",
        "first_appearance_chapter": "ch001",
    },
    {
        "character_id": "char_lead",
        "name": "林晚",
        "role": "女主/利益与情感夹缝中的选择者",
        "relationship": "与男主有旧情，被家族和反派裹挟",
        "motivation": "保护家族，同时确认男主是否值得信任",
        "visual_consistency_prompt": "young Chinese woman, elegant white suit, conflicted eyes, delicate makeup, urban luxury short drama, photorealistic",
        "voice_profile": "清冷但有情绪裂缝",
        "first_appearance_chapter": "ch001",
    },
    {
        "character_id": "char_rival",
        "name": "顾北辰",
        "role": "反派/权势压迫者",
        "relationship": "觊觎女主并试图踩垮男主",
        "motivation": "借联姻和资本控制局面",
        "visual_consistency_prompt": "arrogant Chinese businessman, expensive dark suit, cold smile, luxury banquet lighting, villain aura, photorealistic",
        "voice_profile": "傲慢、压迫感强",
        "first_appearance_chapter": "ch001",
    },
]

PURPOSES = [
    "opening_hook",
    "conflict_escalation",
    "emotional_pressure",
    "conflict_escalation",
    "emotional_pressure",
    "reversal",
    "conflict_escalation",
    "payoff",
    "transition",
    "cliffhanger",
]

FRAMINGS = [
    "close_up",
    "medium_shot",
    "over_the_shoulder",
    "insert_shot",
    "medium_shot",
    "close_up",
    "wide_shot",
    "close_up",
    "medium_shot",
    "extreme_close_up",
]

CAMERA_MOVES = [
    "fast push-in",
    "handheld follow",
    "slow dolly in",
    "snap zoom",
    "static tense framing",
    "dramatic orbit",
    "wide reveal",
    "fast cut close-up",
    "tracking shot",
    "freeze-frame push-in",
]


def build_offline_script(
    chapters: list[Chapter],
    *,
    title: str,
    genre: str,
    tone: str,
    shots_per_episode: int = 10,
) -> dict:
    characters = [dict(character) for character in DEFAULT_CHARACTERS]
    for character in characters:
        character["first_appearance_chapter"] = chapters[0].chapter_id

    episodes: list[dict] = []
    source_map: list[dict] = []
    for episode_index, chapter in enumerate(chapters, start=1):
        shots = _build_episode_shots(chapter, episode_index, shots_per_episode)
        episodes.append(
            {
                "episode_number": episode_index,
                "episode_title": _episode_title(chapter, episode_index),
                "source_chapter_id": chapter.chapter_id,
                "hook_summary": "开场三秒制造当众压迫，把原文冲突提前到观众眼前。",
                "emotional_curve": ["受辱", "隐忍", "逼问", "反转", "悬念"],
                "cliffhanger": "关键证据即将曝光，但真正的幕后人物还没有现身。",
                "estimated_duration_seconds": sum(shot["duration_seconds"] for shot in shots),
                "shots": shots,
            }
        )
        source_map.append(
            {
                "map_id": f"map_ep{episode_index:02d}",
                "target_path": f"episodes[{episode_index - 1}]",
                "chapter_id": chapter.chapter_id,
                "chapter_title": chapter.title,
                "source_excerpt": _excerpt(chapter.text, 260),
                "adaptation_note": "按短剧节奏提取冲突、反转和悬念，保留原文关键事件。",
            }
        )
        for shot_index, shot in enumerate(shots):
            source_map.append(
                {
                    "map_id": f"map_ep{episode_index:02d}_shot{shot_index + 1:02d}",
                    "target_path": f"episodes[{episode_index - 1}].shots[{shot_index}]",
                    "chapter_id": chapter.chapter_id,
                    "chapter_title": chapter.title,
                    "source_excerpt": shot["source_ref"]["source_excerpt"],
                    "adaptation_note": f"将章节事件压缩为第 {shot_index + 1} 个可视化镜头。",
                }
            )

    return {
        "series_metadata": {
            "schema_version": "1.0.0",
            "title": title or "未命名网文短剧改编",
            "author": None,
            "source_type": "web_novel",
            "target_format": "vertical_short_drama",
            "genre": genre,
            "tone": tone,
            "language": "zh-CN",
            "aspect_ratio": "9:16",
            "episode_duration_target": "60-120s",
        },
        "characters": characters,
        "episodes": episodes,
        "source_map": source_map,
        "production_notes": [
            "离线 demo 生成器用于无 API key 演示；正式生成时请启用 DeepSeek/兼容 API。",
            "所有 video_prompt 已按英文视频模型提示词格式输出，可继续接图生视频或分镜工具。",
        ],
    }


def _build_episode_shots(chapter: Chapter, episode_index: int, shots_per_episode: int) -> list[dict]:
    sentences = _sentences(chapter.text)
    if not sentences:
        sentences = [chapter.text]

    shots: list[dict] = []
    middle_purposes = [
        "conflict_escalation",
        "emotional_pressure",
        "conflict_escalation",
        "emotional_pressure",
        "reversal",
        "conflict_escalation",
        "payoff",
        "transition",
    ]
    for shot_index in range(shots_per_episode):
        sentence = sentences[min(shot_index, len(sentences) - 1)]
        if shot_index == 0:
            purpose = "opening_hook"
        elif shot_index == shots_per_episode - 1:
            purpose = "cliffhanger"
        else:
            purpose = middle_purposes[(shot_index - 1) % len(middle_purposes)]
        shot_id = f"ep{episode_index:02d}_s{shot_index + 1:02d}"
        shots.append(
            {
                "shot_id": shot_id,
                "duration_seconds": 5.0 + (shot_index % 3),
                "purpose": purpose,
                "characters": ["沈砚", "林晚"] if shot_index % 3 else ["沈砚", "林晚", "顾北辰"],
                "visual_track": {
                    "framing": FRAMINGS[min(shot_index, len(FRAMINGS) - 1)],
                    "camera_movement": CAMERA_MOVES[min(shot_index, len(CAMERA_MOVES) - 1)],
                    "visual_notes_zh": _visual_note(purpose, sentence),
                    "video_prompt": _video_prompt(purpose, shot_index),
                },
                "audio_track": {
                    "dialogue": [_dialogue_line(purpose, shot_index)],
                    "sfx": _sfx(purpose),
                    "music": "紧张都市短剧鼓点，低频持续推进",
                },
                "source_ref": {
                    "chapter_id": chapter.chapter_id,
                    "chapter_title": chapter.title,
                    "source_excerpt": _excerpt(sentence or chapter.text, 220),
                },
            }
        )
    return shots


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[。！？!?])", text) if part.strip()]


def _excerpt(text: str, limit: int) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) < 10:
        clean = f"{clean} 原文片段较短，需要作者在编辑时补充上下文。"
    return clean[:limit] or "原文片段缺失，需要作者补充。"


def _episode_title(chapter: Chapter, episode_index: int) -> str:
    title = chapter.title.strip()
    if title.startswith("自动切分"):
        return f"第 {episode_index} 集：风暴开场"
    return f"第 {episode_index} 集：{title}"


def _visual_note(purpose: str, source_sentence: str) -> str:
    templates = {
        "opening_hook": "把原文冲突提前：人物被当众逼问，镜头直接贴脸制造压迫。",
        "conflict_escalation": "双方站位形成权力差，反派压近，主角保持沉默但握紧拳头。",
        "emotional_pressure": "用特写表现隐忍，避免抽象心理描写。",
        "reversal": "主角抬眼反问，旁人表情凝固，局势开始翻转。",
        "payoff": "反派短暂失控，围观者议论，主角夺回主动权。",
        "cliffhanger": "关键证据或身份线索出现，画面停在所有人震惊的一瞬。",
        "transition": "用快切交代场景变化，把信息压缩到动作中。",
    }
    return f"{templates.get(purpose, '保留原文动作并转成可拍画面')} 来源：{_excerpt(source_sentence, 90)}"


def _video_prompt(purpose: str, shot_index: int) -> str:
    base = {
        "opening_hook": "A tense vertical short drama opening, a young Chinese man is publicly humiliated at a luxury banquet, shocked faces around him, dramatic lighting, fast push-in camera, photorealistic, 9:16",
        "conflict_escalation": "Urban Chinese short drama scene, arrogant businessman stepping closer while the hero stays silent, strong contrast lighting, handheld camera tension, photorealistic, vertical 9:16",
        "emotional_pressure": "Close-up of a restrained young man with red eyes and clenched jaw, rain-like reflections on glass, cinematic shallow depth of field, photorealistic vertical drama frame",
        "reversal": "The hero suddenly raises his eyes and challenges everyone, guests freeze in surprise, dramatic spotlight, slow dolly in, realistic vertical short drama",
        "payoff": "A villain loses control as the crowd whispers, the hero stands calm in the center, luxury interior, sharp cinematic cuts, photorealistic 9:16 video prompt",
        "cliffhanger": "Extreme close-up of a phone screen revealing a shocking secret document, everyone gasps in the background, suspense lighting, freeze-frame push-in, vertical 9:16",
        "transition": "Fast transition shot through a luxury hallway, urgent footsteps, neon city reflections, dynamic tracking camera, photorealistic vertical short drama",
    }
    prompt = base.get(purpose, base["conflict_escalation"])
    return f"{prompt}, shot number {shot_index + 1}, high detail, vertical 9:16 aspect ratio"


def _dialogue_line(purpose: str, shot_index: int) -> dict:
    if purpose == "opening_hook":
        return {"speaker": "顾北辰", "text": "你还敢站在这里？今天就让所有人看清你是什么人。", "tts_emotion": "傲慢、压迫"}
    if purpose == "reversal":
        return {"speaker": "沈砚", "text": "你确定，要当着所有人的面把真相说完吗？", "tts_emotion": "克制、冷"}
    if purpose == "cliffhanger":
        return {"speaker": "林晚", "text": "这份文件……为什么会有你的名字？", "tts_emotion": "震惊、颤抖"}
    if shot_index % 2:
        return {"speaker": "林晚", "text": "够了，我只想听一句实话。", "tts_emotion": "压抑、动摇"}
    return {"speaker": "沈砚", "text": "我忍到现在，不是因为我怕你们。", "tts_emotion": "低沉、隐忍"}


def _sfx(purpose: str) -> list[str]:
    if purpose == "opening_hook":
        return ["酒杯落地声", "人群倒吸冷气"]
    if purpose == "cliffhanger":
        return ["手机提示音", "音乐骤停"]
    if purpose == "reversal":
        return ["低频鼓点加强", "远处闪光灯声"]
    return ["紧张环境底噪"]
