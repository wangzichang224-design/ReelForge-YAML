from __future__ import annotations

from dataclasses import dataclass

from .critic import CriticResult, ScriptCritic
from .evaluator import ABSTRACT_TERMS, CONFLICT_TERMS, evaluate_document
from .llm_client import LLMConfig, OpenAICompatibleJSONClient
from .schema import Episode, ScriptDocument, Shot
from .scratchpad import inject_visual_traits_into_prompts


@dataclass(frozen=True)
class IterationResult:
    document: ScriptDocument
    critic_result: CriticResult
    rounds_used: int


def run_critic_generator_loop(
    document: ScriptDocument,
    *,
    input_chapter_count: int,
    structural_warnings: list[str] | None = None,
    max_rounds: int = 2,
    client: OpenAICompatibleJSONClient | None = None,
    config: LLMConfig | None = None,
    use_llm_critic: bool = False,
) -> IterationResult:
    critic = ScriptCritic()
    current = inject_visual_traits_into_prompts(document)
    result = critic.review(
        current,
        input_chapter_count=input_chapter_count,
        structural_warnings=structural_warnings,
        client=client,
        config=config,
        use_llm=use_llm_critic,
    )

    rounds_used = 0
    while rounds_used < max_rounds and _needs_rewrite(result):
        current = _rewrite_badcases(current, result)
        current = inject_visual_traits_into_prompts(current)
        rounds_used += 1
        result = critic.review(
            current,
            input_chapter_count=input_chapter_count,
            structural_warnings=structural_warnings,
            client=client,
            config=config,
            use_llm=use_llm_critic,
        )

    return IterationResult(
        document=current.model_copy(update={"quality_report": result.report}),
        critic_result=result,
        rounds_used=rounds_used,
    )


def _needs_rewrite(result: CriticResult) -> bool:
    return any(
        badcase.metric in {"hook", "cliffhanger", "visual_executability"}
        for badcase in result.report.badcases
    )


def _rewrite_badcases(document: ScriptDocument, result: CriticResult) -> ScriptDocument:
    hook_failures = {
        int(badcase.target_path.split("episodes[", 1)[1].split("]", 1)[0])
        for badcase in result.report.badcases
        if badcase.metric == "hook" and "episodes[" in badcase.target_path
    }
    visual_failures = {
        _parse_shot_path(badcase.target_path)
        for badcase in result.report.badcases
        if badcase.metric == "visual_executability"
    }
    episodes: list[Episode] = []
    for episode_index, episode in enumerate(document.episodes):
        updated = episode
        if episode_index in hook_failures:
            updated = _rewrite_opening_hook(updated)
        updated = _rewrite_visual_prompts(updated, episode_index, visual_failures, document)
        episodes.append(updated)
    return document.model_copy(update={"episodes": episodes})


def _rewrite_opening_hook(episode: Episode) -> Episode:
    candidate_index = _find_best_hook_candidate(episode)
    if candidate_index == 0:
        first = _make_first_shot_more_confrontational(episode.shots[0])
        shots = [first, *episode.shots[1:]]
    else:
        shots = list(episode.shots)
        candidate = _make_first_shot_more_confrontational(shots[candidate_index])
        original_first = shots[0].model_copy(
            update={
                "purpose": "emotional_pressure",
                "shot_id": shots[0].shot_id,
            }
        )
        shots[0] = candidate.model_copy(update={"purpose": "opening_hook", "shot_id": episode.shots[0].shot_id})
        shots[candidate_index] = original_first.model_copy(update={"shot_id": episode.shots[candidate_index].shot_id})
    return episode.model_copy(update={"shots": shots})


def _find_best_hook_candidate(episode: Episode) -> int:
    best_index = 0
    best_score = -1
    for index, shot in enumerate(episode.shots[:6]):
        text = " ".join(
            [
                shot.visual_track.visual_notes_zh,
                shot.visual_track.video_prompt,
                " ".join(line.text for line in shot.audio_track.dialogue),
                shot.source_ref.source_excerpt,
            ]
        ).lower()
        score = sum(1 for term in CONFLICT_TERMS if term.lower() in text)
        if shot.audio_track.dialogue:
            score += 1
        if shot.purpose in {"conflict_escalation", "reversal", "payoff"}:
            score += 1
        if score > best_score:
            best_score = score
            best_index = index
    return best_index


def _make_first_shot_more_confrontational(shot: Shot) -> Shot:
    visual_track = shot.visual_track.model_copy(
        update={
            "framing": "close_up",
            "camera_movement": "fast push-in",
            "visual_notes_zh": (
                "黄金三秒：直接切入当众羞辱、证据逼问或权力压迫，人物正面冲突先于环境铺垫。"
                f" 原镜头：{shot.visual_track.visual_notes_zh}"
            ),
            "video_prompt": _confrontational_prompt(shot),
        }
    )
    audio_track = shot.audio_track
    if not audio_track.dialogue:
        audio_track = audio_track.model_copy(
            update={
                "sfx": ["sharp impact sting", *audio_track.sfx],
                "music": audio_track.music or "urgent short-drama tension hit",
            }
        )
    return shot.model_copy(update={"visual_track": visual_track, "audio_track": audio_track})


def _confrontational_prompt(shot: Shot) -> str:
    character_hint = ", ".join(shot.characters[:3]) or "main characters"
    return (
        "Close-up shot, fast push-in camera, a public confrontation erupts in the first three seconds, "
        f"{character_hint} face each other under harsh dramatic lighting, one character points at evidence or blocks the other, "
        "shocked bystanders in the background, concrete gestures, vertical 9:16, high-tension short drama style. "
        f"Source action: {shot.visual_track.video_prompt}"
    )


def _rewrite_visual_prompts(
    episode: Episode,
    episode_index: int,
    visual_failures: set[tuple[int, int] | None],
    document: ScriptDocument,
) -> Episode:
    shots = []
    scene_hint = _scene_hint(document)
    for shot_index, shot in enumerate(episode.shots):
        if (episode_index, shot_index) in visual_failures:
            visual_track = shot.visual_track.model_copy(
                update={
                    "visual_notes_zh": (
                        f"把抽象情绪改为可见动作：人物在{scene_hint}中站定，手持道具或证据，"
                        "通过指向、阻拦、对视、屏幕信息或文件特写表现压力。"
                    ),
                    "video_prompt": (
                        f"{shot.visual_track.framing.replace('_', ' ')} shot, {shot.visual_track.camera_movement}, "
                        f"in {scene_hint}, "
                        "the character is standing, holding a visible prop, pointing or looking at evidence, "
                        "visible facial expression, cinematic lighting, vertical 9:16. "
                        f"{_sanitize_abstract_prompt(shot.visual_track.video_prompt)}"
                    )
                }
            )
            shot = shot.model_copy(update={"visual_track": visual_track})
        shots.append(shot)
    return episode.model_copy(update={"shots": shots})


def _scene_hint(document: ScriptDocument) -> str:
    if document.visual_bible:
        if document.visual_bible.key_locations:
            first_location = document.visual_bible.key_locations[0]
            return f"a specific {first_location} scene interior"
        style = document.visual_bible.global_style.lower()
    else:
        style = document.series_metadata.genre.lower()
    if any(term in style for term in ["古风", "宫", "palace", "ancient"]):
        return "a palace interior with lanterns and officials"
    if any(term in style for term in ["医疗", "病房", "hospital"]):
        return "a hospital ward interior with monitors and medical props"
    if any(term in style for term in ["职场", "客服", "office", "refund"]):
        return "a customer service office with computer screens"
    return "a modern short drama interior"


def _sanitize_abstract_prompt(prompt: str) -> str:
    cleaned = prompt
    for term in ABSTRACT_TERMS:
        cleaned = cleaned.replace(term, "visible facial reaction")
        cleaned = cleaned.replace(term.title(), "visible facial reaction")
    return cleaned


def _parse_shot_path(path: str) -> tuple[int, int] | None:
    try:
        episode_index = int(path.split("episodes[", 1)[1].split("]", 1)[0])
        shot_index = int(path.split("shots[", 1)[1].split("]", 1)[0])
        return episode_index, shot_index
    except (IndexError, ValueError):
        return None


def score_document_after_iteration(document: ScriptDocument) -> ScriptDocument:
    report = evaluate_document(document, visual_bible=document.visual_bible)
    return document.model_copy(update={"quality_report": report})
