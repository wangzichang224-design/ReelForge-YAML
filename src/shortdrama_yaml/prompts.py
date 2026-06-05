from __future__ import annotations

import json

from .chapter_parser import Chapter
from .schema import script_json_schema


SYSTEM_PROMPT = """你是一个顶级竖屏短剧改编导演、编剧和 AI 视频提示词工程师。

你的任务：把 3 个以上网文章节转换为严格 JSON。注意：必须输出 json object，不要输出 Markdown，不要输出解释文字。

改编原则：
1. 面向 9:16 竖屏短剧，不是传统影视剧本。每集开场前三秒必须有强冲突。
2. 删除冗长心理描写，把心理活动翻译为可见动作、表情、站位、道具、光影和声音。
3. 每章默认改编为 1 集，每集 10-15 个 shots，第一镜头 purpose 必须是 opening_hook，最后一镜头 purpose 必须是 cliffhanger。
4. 严格音画分离：visual_track 只写画面和运镜；audio_track 写台词、音效、音乐。
5. visual_track.video_prompt 必须是英文，适合 Kling/Runway/可灵/即梦等视频模型，包含主体、动作、场景、光影、竖屏 9:16。
6. 禁止在 video_prompt 中用 inner thought、complex emotion、heartbroken、暗自盘算、心如死灰等抽象词替代动作。
7. 低冲突章节必须把手机、屏幕、账单、录音、监控、文件、针管、印章等道具前置成可拍镜头。
8. 每个 episode 和 shot 必须保留 source_ref/source_map，用原文片段证明改编来源，禁止凭空新增关键剧情。
9. 作者拿到 YAML 后要能继续人工编辑，所以字段要清晰、短句化、可复用。
"""


def build_generation_prompt(
    chapters: list[Chapter],
    *,
    title: str,
    genre: str,
    tone: str,
    target_style: str,
    shots_per_episode: int,
) -> str:
    chapter_payload = [
        {
            "chapter_id": chapter.chapter_id,
            "title": chapter.title,
            "text": _clip_chapter(chapter.text),
        }
        for chapter in chapters
    ]

    request_payload = {
        "task": "convert_web_novel_chapters_to_vertical_short_drama_yaml_json_source",
        "series_title": title,
        "genre": genre,
        "tone": tone,
        "target_style": target_style,
        "shots_per_episode": shots_per_episode,
        "hard_constraints": [
            f"每一集 shots 数量必须恰好为 {shots_per_episode} 个，不能少于 {shots_per_episode} 个，也不能多于 {shots_per_episode} 个。",
            "每一集第 1 个 shot 的 purpose 必须是 opening_hook。",
            "每一集最后 1 个 shot 的 purpose 必须是 cliffhanger。",
            "每个 shot 必须包含 visual_track、audio_track、source_ref。",
            "visual_track.video_prompt 必须为英文，并显式包含 vertical 9:16 或 9:16。",
            "visual_track.video_prompt 必须包含 shot type、主体、具体动作、场景/环境、camera movement 或 lighting。",
            "不要输出 inner thought、complex emotion、heartbroken 等抽象文学 video_prompt。",
            "遇到平淡内心独白或低冲突段落时，必须改写为屏幕信息、录音、文件、监控、账单、电话、针管、印章等可见道具动作。",
            "不要为了节省篇幅省略镜头；即使剧情短，也必须拆成足够数量的可拍镜头。",
        ],
        "input_chapter_count": len(chapters),
        "chapters": chapter_payload,
        "required_json_schema": script_json_schema(),
    }
    return (
        "请根据下面的 json 请求，输出一个严格匹配 required_json_schema 的 JSON object。\n"
        "不要输出 Markdown，不要包裹 ```json，不要输出 YAML。\n\n"
        + json.dumps(request_payload, ensure_ascii=False, indent=2)
    )


def build_repair_prompt(payload: dict, validation_error: str) -> str:
    expected_shots = _infer_expected_shots(payload)
    repair_payload = {
        "task": "repair_invalid_short_drama_script_json",
        "validation_error": validation_error,
        "hard_repair_rules": [
            f"重点修复：每个 episode.shots 必须补足到 {expected_shots} 个 shot。",
            "不要删除 episode；不要删除 source_map。",
            "补充镜头时必须使用同一章节的 source_excerpt，并保持 opening_hook 和 cliffhanger 位置。",
            "所有新增 video_prompt 必须是英文，并包含 vertical 9:16。",
            "输出完整 JSON object，不要只输出补丁。",
        ],
        "required_json_schema": script_json_schema(),
        "invalid_json": payload,
    }
    return (
        "下面的 JSON 没有通过 Pydantic/YAML Schema 校验。请只输出修复后的严格 JSON object。\n"
        "不要解释，不要 Markdown，不要丢失 source_map。\n\n"
        + json.dumps(repair_payload, ensure_ascii=False, indent=2)
    )


def _clip_chapter(text: str, limit: int = 6500) -> str:
    clean = text.strip()
    if len(clean) <= limit:
        return clean
    head = clean[: limit // 2]
    tail = clean[-limit // 2 :]
    return f"{head}\n\n...[中间内容为控制上下文已省略，但请保持剧情因果]...\n\n{tail}"


def _infer_expected_shots(payload: dict) -> int:
    episodes = payload.get("episodes", [])
    shot_counts = [
        len(episode.get("shots", []))
        for episode in episodes
        if isinstance(episode, dict) and isinstance(episode.get("shots"), list)
    ]
    if not shot_counts:
        return 10
    return max(10, min(15, max(shot_counts + [10])))
