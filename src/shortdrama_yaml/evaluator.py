from __future__ import annotations

import re
from statistics import mean

from .schema import (
    Episode,
    EpisodeQualityScore,
    QualityBadcase,
    QualityReport,
    ScriptDocument,
    Shot,
    VisualBible,
)


CONFLICT_TERMS = {
    "humiliate",
    "humiliated",
    "accuse",
    "accusing",
    "argue",
    "threat",
    "threaten",
    "slap",
    "block",
    "blocking",
    "tearing",
    "evidence",
    "betray",
    "shout",
    "confront",
    "conflict",
    "insult",
    "羞辱",
    "陷害",
    "逼问",
    "质问",
    "威胁",
    "撕",
    "支票",
    "证据",
    "拦",
    "反咬",
    "当众",
}

CLIFFHANGER_TERMS = {
    "secret",
    "anonymous",
    "reveal",
    "about to",
    "crisis",
    "evidence",
    "identity",
    "fingerprint",
    "private computer",
    "betray",
    "truth",
    "短信",
    "匿名",
    "真相",
    "身份",
    "证据",
    "危机",
    "签字人",
    "幕后",
    "即将",
    "买不起",
    "指纹",
    "私人电脑",
}

EXECUTABLE_TERMS = {
    "close-up",
    "close up",
    "medium shot",
    "wide shot",
    "over-the-shoulder",
    "insert shot",
    "camera",
    "lighting",
    "vertical",
    "9:16",
    "shot",
}

CAMERA_LIGHT_TERMS = {
    "camera",
    "lighting",
    "light",
    "push-in",
    "dolly",
    "handheld",
    "tracking",
    "freeze-frame",
    "cinematic",
}

CONCRETE_ACTION_TERMS = {
    "holding",
    "walking",
    "standing",
    "tearing",
    "pushing",
    "falling",
    "gripping",
    "blocking",
    "showing",
    "pressing",
    "reaching",
    "looking",
    "turning",
    "holding up",
    "points",
    "pointing",
    "blocks",
    "shows",
    "raises",
    "grabs",
    "typing",
    "clicking",
    "recording",
}

SCENE_TERMS = {
    "banquet",
    "hospital",
    "office",
    "meeting room",
    "palace",
    "gate",
    "warehouse",
    "screen",
    "hallway",
    "street",
    "car",
    "room",
    "background",
    "interior",
}

ABSTRACT_TERMS = {
    "inner thought",
    "complex emotion",
    "heartbroken",
    "暗自",
    "心如死灰",
    "内心",
    "复杂",
    "心理",
    "情绪复杂",
    "三分",
    "凉薄",
    "漫不经心",
}

INVENTED_SOURCE_TERMS = {
    "原文未直接描述",
    "改编自情境",
    "原文片段缺失",
}


def evaluate_document(
    document: ScriptDocument,
    *,
    input_chapter_count: int | None = None,
    structural_warnings: list[str] | None = None,
    visual_bible: VisualBible | None = None,
) -> QualityReport:
    visual_bible = visual_bible or document.visual_bible
    warnings = list(structural_warnings or [])
    episode_scores: list[EpisodeQualityScore] = []
    badcases: list[QualityBadcase] = []

    for episode_index, episode in enumerate(document.episodes):
        score, episode_badcases = evaluate_episode(
            episode,
            episode_index=episode_index,
            visual_bible=visual_bible,
        )
        episode_scores.append(score)
        badcases.extend(episode_badcases)

    overall_score = mean([score.overall_score for score in episode_scores]) if episode_scores else 0.0
    root_causes = _unique([badcase.root_cause for badcase in badcases])
    repair_suggestions = _unique([badcase.repair_suggestion for badcase in badcases])
    if badcases:
        warnings.extend(
            f"{badcase.metric}:{badcase.target_path} - {badcase.reason}"
            for badcase in badcases
        )

    return QualityReport(
        input_chapter_count=input_chapter_count if input_chapter_count is not None else len(document.episodes),
        total_episodes=len(document.episodes),
        total_shots=sum(len(episode.shots) for episode in document.episodes),
        schema_valid=True,
        warnings=warnings,
        overall_score=round(overall_score, 3),
        episode_scores=episode_scores,
        badcases=badcases,
        root_causes=root_causes,
        repair_suggestions=repair_suggestions,
    )


def evaluate_episode(
    episode: Episode,
    *,
    episode_index: int,
    visual_bible: VisualBible | None = None,
) -> tuple[EpisodeQualityScore, list[QualityBadcase]]:
    badcases: list[QualityBadcase] = []
    hook_score = _score_opening_hook(episode)
    cliffhanger_score = _score_cliffhanger(episode)
    power_shift_score = _score_power_shift(episode)
    visual_score, visual_badcases = _score_visual_executability(episode, episode_index)
    continuity_score, continuity_badcases = _score_continuity(episode, episode_index, visual_bible)
    provenance_score, provenance_badcases = _score_provenance(episode, episode_index)
    dialogue_score, dialogue_badcases = _score_dialogue_language(episode, episode_index)
    badcases.extend(visual_badcases)
    badcases.extend(continuity_badcases)
    badcases.extend(provenance_badcases)
    badcases.extend(dialogue_badcases)

    if hook_score < 0.75:
        first = episode.shots[0]
        badcases.append(
            QualityBadcase(
                metric="hook",
                severity="high",
                target_path=f"episodes[{episode_index}].shots[0]",
                reason="首镜头虽然标记 opening_hook，但画面/台词没有直接出现羞辱、逼问、证据冲突或压迫动作。",
                root_cause="生成模型把开场写成氛围铺垫，而不是短剧黄金三秒冲突。",
                repair_suggestion="把原文中最强的对峙、羞辱、证据揭露或威胁台词提前到第 1 个镜头。",
                source_excerpt=first.source_ref.source_excerpt,
            )
        )

    if cliffhanger_score < 0.75:
        last_index = len(episode.shots) - 1
        badcases.append(
            QualityBadcase(
                metric="cliffhanger",
                severity="high",
                target_path=f"episodes[{episode_index}].shots[{last_index}]",
                reason="结尾没有卡在真相即将揭晓、身份暴露、危机降临或反派反扑之前。",
                root_cause="episode cliffhanger 描述偏总结，没有形成骗氪式下一集驱动力。",
                repair_suggestion="把结尾改为短信、文件、电话、身份线索或突发危机出现的一瞬间。",
                source_excerpt=episode.shots[-1].source_ref.source_excerpt,
            )
        )

    if power_shift_score < 0.75:
        badcases.append(
            QualityBadcase(
                metric="power_shift",
                severity="medium",
                target_path=f"episodes[{episode_index}]",
                reason="本集缺少明确的掌控权变化。",
                root_cause="镜头只是顺叙事件，没有设置 reversal/payoff 节点。",
                repair_suggestion="至少加入一个从被压迫者夺回主动权、证据反咬或反派失控的镜头。",
                source_excerpt=episode.shots[0].source_ref.source_excerpt,
            )
        )

    scores = [
        hook_score,
        cliffhanger_score,
        power_shift_score,
        visual_score,
        continuity_score,
        provenance_score,
        dialogue_score,
    ]
    overall_score = round(mean(scores), 3)
    score = EpisodeQualityScore(
        episode_number=episode.episode_number,
        hook_score=round(hook_score, 3),
        cliffhanger_score=round(cliffhanger_score, 3),
        power_shift_score=round(power_shift_score, 3),
        visual_executability_score=round(visual_score, 3),
        continuity_score=round(continuity_score, 3),
        provenance_score=round(provenance_score, 3),
        dialogue_language_score=round(dialogue_score, 3),
        overall_score=overall_score,
        passed=overall_score >= 0.8
        and hook_score >= 0.75
        and cliffhanger_score >= 0.75
        and visual_score >= 0.75
        and dialogue_score >= 0.75,
        cliffhanger_options=build_cliffhanger_options(episode),
    )
    return score, badcases


def build_cliffhanger_options(episode: Episode) -> list[str]:
    base = episode.cliffhanger.strip()
    hero = episode.shots[-1].characters[0] if episode.shots[-1].characters else "主角"
    return [
        f"身份曝光型：{hero} 刚要离开，屏幕弹出一份能证明真实身份的文件，所有人同时噤声。",
        f"危机降临型：{base} 下一秒，电话那头传来警方/医院/董事会的紧急通告。",
        f"反派反扑型：{base} 镜头切到反派冷笑，他手里还有一份足以反咬主角的证据。",
    ]


def _score_opening_hook(episode: Episode) -> float:
    if not episode.shots:
        return 0.0
    first = episode.shots[0]
    text = _shot_text(first)
    keyword_score = _contains_any(text, CONFLICT_TERMS)
    dialogue_bonus = 0.2 if first.audio_track.dialogue else 0.0
    action_bonus = 0.15 if _contains_any(text, CONCRETE_ACTION_TERMS) else 0.0
    purpose_bonus = 0.2 if first.purpose == "opening_hook" else 0.0
    return min(1.0, (0.45 if keyword_score else 0.0) + dialogue_bonus + action_bonus + purpose_bonus)


def _score_cliffhanger(episode: Episode) -> float:
    if not episode.shots:
        return 0.0
    last = episode.shots[-1]
    text = " ".join([episode.cliffhanger, _shot_text(last)]).lower()
    purpose_bonus = 0.3 if last.purpose == "cliffhanger" else 0.0
    cliff_bonus = 0.45 if _contains_any(text, CLIFFHANGER_TERMS) else 0.0
    question_bonus = 0.15 if "?" in text or "？" in text else 0.0
    source_bonus = 0.1 if len(last.source_ref.source_excerpt) >= 10 else 0.0
    return min(1.0, purpose_bonus + cliff_bonus + question_bonus + source_bonus)


def _score_power_shift(episode: Episode) -> float:
    purposes = [shot.purpose for shot in episode.shots]
    has_reversal = any(purpose in {"reversal", "payoff"} for purpose in purposes)
    curve_text = " ".join(episode.emotional_curve)
    curve_shift = any(term in curve_text for term in ["反转", "揭露", "打脸", "失控", "夺回", "震惊"])
    return 1.0 if has_reversal and curve_shift else 0.75 if has_reversal else 0.35


def _score_visual_executability(
    episode: Episode,
    episode_index: int,
) -> tuple[float, list[QualityBadcase]]:
    badcases: list[QualityBadcase] = []
    shot_scores: list[float] = []
    for shot_index, shot in enumerate(episode.shots):
        prompt = shot.visual_track.video_prompt.lower()
        notes = shot.visual_track.visual_notes_zh
        has_shot_type = any(term in prompt for term in EXECUTABLE_TERMS)
        has_action = any(term in prompt for term in CONCRETE_ACTION_TERMS)
        has_scene = any(term in prompt for term in SCENE_TERMS)
        has_camera_or_light = any(term in prompt for term in CAMERA_LIGHT_TERMS)
        has_aspect = "9:16" in prompt or "vertical" in prompt
        has_abstract = _contains_any(prompt, ABSTRACT_TERMS) or _contains_any(notes, ABSTRACT_TERMS)
        score = (
            0.2
            + (0.2 if has_shot_type else 0.0)
            + (0.25 if has_action else 0.0)
            + (0.15 if has_scene else 0.0)
            + (0.15 if has_camera_or_light else 0.0)
            + (0.1 if has_aspect else 0.0)
            - (0.5 if has_abstract else 0.0)
        )
        score = max(0.0, min(1.0, score))
        shot_scores.append(score)
        if score < 0.75:
            badcases.append(
                QualityBadcase(
                    metric="visual_executability",
                    severity="high" if has_abstract else "medium",
                    target_path=f"episodes[{episode_index}].shots[{shot_index}].visual_track.video_prompt",
                    reason="video_prompt 缺少完整视频提示词语法，或含抽象文学表达。",
                    root_cause="文学描写没有充分转译为摄影机可捕捉的动作、构图、光影和道具。",
                    repair_suggestion="改写为 shot type + subject + concrete action + scene/environment + camera/lighting + vertical 9:16。",
                    source_excerpt=shot.source_ref.source_excerpt,
                )
            )
    return mean(shot_scores) if shot_scores else 0.0, badcases


def _score_continuity(
    episode: Episode,
    episode_index: int,
    visual_bible: VisualBible | None,
) -> tuple[float, list[QualityBadcase]]:
    if not visual_bible or not visual_bible.characters:
        return 0.85, []
    badcases: list[QualityBadcase] = []
    checked = 0
    passed = 0
    assets = {asset.character_id: asset for asset in visual_bible.characters}
    allowed_drift_terms = _allowed_drift_terms(visual_bible)
    for shot_index, shot in enumerate(episode.shots):
        prompt = shot.visual_track.video_prompt.lower()
        for character_id in shot.characters:
            asset = assets.get(character_id)
            if not asset:
                continue
            checked += 1
            prompt_hits = sum(1 for trait in asset.locked_traits if trait.lower() in prompt)
            drift_hits = [
                term
                for term in asset.negative_drift_terms
                if term.lower() in prompt and term.lower() not in allowed_drift_terms
            ]
            if prompt_hits >= 1 and not drift_hits:
                passed += 1
            else:
                badcases.append(
                    QualityBadcase(
                        metric="continuity",
                        severity="medium",
                        target_path=f"episodes[{episode_index}].shots[{shot_index}]",
                        reason=f"{asset.name} 的镜头没有稳定继承视觉资产，或出现外观漂移。",
                        root_cause="生成镜头时未强制注入全局角色视觉黑板。",
                        repair_suggestion=f"在 video_prompt 中加入角色固定特征：{asset.visual_prompt}",
                        source_excerpt=shot.source_ref.source_excerpt,
                    )
                )
    if checked == 0:
        return 0.85, []
    return passed / checked, badcases[:8]


def _score_dialogue_language(
    episode: Episode,
    episode_index: int,
) -> tuple[float, list[QualityBadcase]]:
    badcases: list[QualityBadcase] = []
    dialogue_lines = [
        line
        for shot in episode.shots
        for line in shot.audio_track.dialogue
    ]
    if not dialogue_lines:
        return 0.0, [
            QualityBadcase(
                metric="dialogue_language",
                severity="medium",
                target_path=f"episodes[{episode_index}].audio_track.dialogue",
                reason="本集没有可用中文台词。",
                root_cause="剧本过度依赖画面描述，缺少短剧对抗台词。",
                repair_suggestion="至少为 opening_hook、reversal 和 cliffhanger 镜头补充中文台词。",
            )
        ]

    passed = 0
    for line in dialogue_lines:
        cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", line.text))
        ascii_letters = len(re.findall(r"[A-Za-z]", line.text))
        if cjk_chars >= 2 and cjk_chars >= ascii_letters:
            passed += 1
    score = passed / len(dialogue_lines)
    if score < 0.75:
        badcases.append(
            QualityBadcase(
                metric="dialogue_language",
                severity="medium",
                target_path=f"episodes[{episode_index}].audio_track.dialogue",
                reason="本集台词不是以中文为主，或中文短剧对抗台词不足。",
                root_cause="生成模型把作者可编辑的中文对白写成了英文/空白/提示词式文本。",
                repair_suggestion="保留 video_prompt 英文，但 dialogue.text 必须使用中文短句。",
            )
        )
    return score, badcases


def _score_provenance(
    episode: Episode,
    episode_index: int,
) -> tuple[float, list[QualityBadcase]]:
    badcases: list[QualityBadcase] = []
    bad_count = 0
    for shot_index, shot in enumerate(episode.shots):
        excerpt = shot.source_ref.source_excerpt
        if len(excerpt.strip()) < 10 or _contains_any(excerpt, INVENTED_SOURCE_TERMS):
            bad_count += 1
            badcases.append(
                QualityBadcase(
                    metric="provenance",
                    severity="medium",
                    target_path=f"episodes[{episode_index}].shots[{shot_index}].source_ref",
                    reason="source_ref 不是稳定原文片段，可能是模型补写或情境推断。",
                    root_cause="为了补足镜头，模型新增了原文没有直接提供的动作。",
                    repair_suggestion="用同章真实原文片段替换 source_excerpt，或在 adaptation_note 中显式标注改编逻辑。",
                    source_excerpt=excerpt,
                )
            )
    if not episode.shots:
        return 0.0, badcases
    return max(0.0, 1.0 - bad_count / len(episode.shots)), badcases


def _contains_any(text: str, terms: set[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _allowed_drift_terms(visual_bible: VisualBible) -> set[str]:
    style = " ".join(
        [
            visual_bible.global_style,
            " ".join(visual_bible.key_locations),
        ]
    ).lower()
    if any(term in style for term in ["古风", "宫", "权谋", "长安", "palace", "ancient"]):
        return {"ancient costume"}
    return set()


def _shot_text(shot: Shot) -> str:
    dialogue = " ".join(line.text for line in shot.audio_track.dialogue)
    sfx = " ".join(shot.audio_track.sfx)
    return " ".join(
        [
            shot.visual_track.visual_notes_zh,
            shot.visual_track.video_prompt,
            shot.visual_track.camera_movement,
            dialogue,
            sfx,
            shot.source_ref.source_excerpt,
        ]
    )


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        normalized = re.sub(r"\s+", " ", item).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            output.append(normalized)
    return output
