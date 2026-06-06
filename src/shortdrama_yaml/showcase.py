from __future__ import annotations

from dataclasses import dataclass

from .schema import Episode, ScriptDocument, Shot


@dataclass(frozen=True)
class ShowcaseShot:
    shot_id: str
    purpose: str
    duration_seconds: float
    framing: str
    camera_movement: str
    subtitle: str
    visual_notes: str
    video_prompt: str
    source_excerpt: str
    source_chapter: str


@dataclass(frozen=True)
class ShowcaseEpisode:
    episode_number: int
    episode_title: str
    hook_summary: str
    cliffhanger: str
    emotional_curve: list[str]
    total_duration_seconds: float
    shots: list[ShowcaseShot]


def build_showcase_episode(document: ScriptDocument, episode_number: int = 1) -> ShowcaseEpisode:
    episode = _find_episode(document, episode_number)
    shots = [_build_showcase_shot(shot) for shot in episode.shots]
    return ShowcaseEpisode(
        episode_number=episode.episode_number,
        episode_title=episode.episode_title,
        hook_summary=episode.hook_summary,
        cliffhanger=episode.cliffhanger,
        emotional_curve=list(episode.emotional_curve),
        total_duration_seconds=sum(shot.duration_seconds for shot in episode.shots),
        shots=shots,
    )


def render_job_demo_script(document: ScriptDocument) -> str:
    title = document.series_metadata.title
    episode_count = len(document.episodes)
    shot_count = sum(len(episode.shots) for episode in document.episodes)
    report = document.quality_report
    score_text = "暂无评分"
    badcase_text = "暂无 badcase 数据"
    if report and report.overall_score is not None:
        score_text = f"{report.overall_score:.3f}"
        badcase_text = f"{len(report.badcases)} 个 hard-rule badcases"

    return f"""大家好，我想用 ReelForge YAML 这个项目展示我对产品经理实习岗位的理解。

我没有把题目简单理解成“让大模型写一段剧本”，而是先做需求分析：小说作者真正缺的不是一段不可控文本，而是一份可编辑、可追溯、可继续打磨的剧本初稿。围绕这个需求，我把产品目标定义为：把 3 章以上小说转换成结构化 YAML，让作者能看到分集、镜头、台词、音效、来源引用和质量提示。

在产品设计上，系统从章节解析开始，生成 {episode_count} 集、{shot_count} 个镜头。每个镜头都拆成 visual_track、audio_track 和 source_ref：visual_track 面向后续 AI 视频或分镜制作，audio_track 面向台词和声音，source_ref 用来降低 AI 编造剧情的风险。

在架构选型上，我采用 JSON-first 到 YAML 的链路：先让模型输出更容易校验的 JSON，再用 Pydantic Schema 做结构约束，最后导出作者更容易编辑的 YAML。这样既保留 AI 效率，也保留工程上的确定性和可维护性。

在代码实现上，我用 Python 和 Streamlit 做了完整闭环，包括章节解析、离线 demo fallback、OpenAI-compatible 调用、Schema 校验、YAML 编辑器、质量评测和 critic loop。这个展示页里的 9:16 预览不真正消耗视频生成额度，而是证明每个镜头已经具备视频生产所需的信息结构。

在复盘沉淀上，我没有只凭主观感受说效果变好，而是做了 golden benchmark。当前项目可以展示综合评分 {score_text}，并记录 {badcase_text}。这对应岗位要求里的复盘沉淀和十倍效率方法论：用数据发现问题，用结构化方案修复问题。

所以这个项目覆盖了需求分析、产品设计、架构选型、代码实现和复盘沉淀。它体现的是我从 0 到 1 推动一个 AI 产品落地的能力，而不是只接收指令写一个工具。"""


def _find_episode(document: ScriptDocument, episode_number: int) -> Episode:
    for episode in document.episodes:
        if episode.episode_number == episode_number:
            return episode
    raise ValueError(f"Episode {episode_number} not found.")


def _build_showcase_shot(shot: Shot) -> ShowcaseShot:
    dialogue = " ".join(line.text for line in shot.audio_track.dialogue).strip()
    subtitle = dialogue or shot.visual_track.visual_notes_zh
    return ShowcaseShot(
        shot_id=shot.shot_id,
        purpose=shot.purpose,
        duration_seconds=shot.duration_seconds,
        framing=shot.visual_track.framing,
        camera_movement=shot.visual_track.camera_movement,
        subtitle=subtitle,
        visual_notes=shot.visual_track.visual_notes_zh,
        video_prompt=shot.visual_track.video_prompt,
        source_excerpt=shot.source_ref.source_excerpt,
        source_chapter=f"{shot.source_ref.chapter_id} · {shot.source_ref.chapter_title}",
    )
