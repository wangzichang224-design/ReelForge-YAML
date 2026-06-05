from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


FrameSize = Literal[
    "extreme_close_up",
    "close_up",
    "medium_shot",
    "wide_shot",
    "over_the_shoulder",
    "insert_shot",
]

ShotPurpose = Literal[
    "opening_hook",
    "conflict_escalation",
    "emotional_pressure",
    "reversal",
    "payoff",
    "cliffhanger",
    "transition",
]

QualityMetric = Literal[
    "hook",
    "cliffhanger",
    "power_shift",
    "visual_executability",
    "continuity",
    "provenance",
    "dialogue_language",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SeriesMetadata(StrictModel):
    schema_version: str = Field(default="1.0.0")
    title: str = Field(min_length=1)
    author: str | None = None
    source_type: str = Field(default="web_novel")
    target_format: str = Field(default="vertical_short_drama")
    genre: str = Field(min_length=1)
    tone: str = Field(min_length=1)
    language: str = Field(default="zh-CN")
    aspect_ratio: Literal["9:16"] = "9:16"
    episode_duration_target: str = Field(default="60-120s")


class Character(StrictModel):
    character_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    relationship: str = Field(min_length=1)
    motivation: str = Field(min_length=1)
    visual_consistency_prompt: str = Field(min_length=20)
    voice_profile: str = Field(min_length=1)
    first_appearance_chapter: str = Field(min_length=1)


class VisualAsset(StrictModel):
    character_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    locked_traits: list[str] = Field(default_factory=list)
    wardrobe: str = Field(default="")
    visual_prompt: str = Field(min_length=20)
    negative_drift_terms: list[str] = Field(default_factory=list)


class VisualBible(StrictModel):
    global_style: str = Field(min_length=1)
    palette: list[str] = Field(default_factory=list)
    key_locations: list[str] = Field(default_factory=list)
    key_props: list[str] = Field(default_factory=list)
    characters: list[VisualAsset] = Field(default_factory=list)


class SourceRef(StrictModel):
    chapter_id: str = Field(min_length=1)
    chapter_title: str = Field(min_length=1)
    source_excerpt: str = Field(min_length=10)

    @field_validator("source_excerpt")
    @classmethod
    def trim_excerpt(cls, value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip()
        return value[:280]


class DialogueLine(StrictModel):
    speaker: str = Field(min_length=1)
    text: str = Field(min_length=1)
    tts_emotion: str = Field(min_length=1)


class VisualTrack(StrictModel):
    framing: FrameSize
    camera_movement: str = Field(min_length=1)
    visual_notes_zh: str = Field(min_length=1)
    video_prompt: str = Field(min_length=20)

    @field_validator("video_prompt")
    @classmethod
    def video_prompt_should_be_english_like(cls, value: str) -> str:
        ascii_letters = len(re.findall(r"[A-Za-z]", value))
        cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", value))
        if ascii_letters < 20 or cjk_chars > ascii_letters:
            raise ValueError(
                "video_prompt should be an English prompt for image/video models"
            )
        return value.strip()


class AudioTrack(StrictModel):
    dialogue: list[DialogueLine] = Field(default_factory=list)
    sfx: list[str] = Field(default_factory=list)
    music: str = Field(default="")


class Shot(StrictModel):
    shot_id: str = Field(min_length=1)
    duration_seconds: float = Field(ge=1.0, le=10.0)
    purpose: ShotPurpose
    characters: list[str] = Field(default_factory=list)
    visual_track: VisualTrack
    audio_track: AudioTrack
    source_ref: SourceRef


class Episode(StrictModel):
    episode_number: int = Field(ge=1)
    episode_title: str = Field(min_length=1)
    source_chapter_id: str = Field(min_length=1)
    hook_summary: str = Field(min_length=1)
    emotional_curve: list[str] = Field(min_length=3)
    cliffhanger: str = Field(min_length=1)
    estimated_duration_seconds: float = Field(ge=30.0, le=180.0)
    shots: list[Shot]

    @model_validator(mode="after")
    def validate_short_drama_density(self) -> "Episode":
        shot_count = len(self.shots)
        if shot_count < 10 or shot_count > 15:
            raise ValueError("each episode must contain 10-15 shots")
        if self.shots[0].purpose != "opening_hook":
            raise ValueError("the first shot must be an opening_hook")
        if self.shots[-1].purpose != "cliffhanger":
            raise ValueError("the last shot must be a cliffhanger")
        return self


class SourceMapEntry(StrictModel):
    map_id: str = Field(min_length=1)
    target_path: str = Field(min_length=1)
    chapter_id: str = Field(min_length=1)
    chapter_title: str = Field(min_length=1)
    source_excerpt: str = Field(min_length=10)
    adaptation_note: str = Field(min_length=1)

    @field_validator("source_excerpt")
    @classmethod
    def trim_excerpt(cls, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()[:320]


class QualityBadcase(StrictModel):
    metric: QualityMetric
    severity: Literal["low", "medium", "high"]
    target_path: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    root_cause: str = Field(min_length=1)
    repair_suggestion: str = Field(min_length=1)
    source_excerpt: str | None = None


class EpisodeQualityScore(StrictModel):
    episode_number: int = Field(ge=1)
    hook_score: float = Field(ge=0, le=1)
    cliffhanger_score: float = Field(ge=0, le=1)
    power_shift_score: float = Field(ge=0, le=1)
    visual_executability_score: float = Field(ge=0, le=1)
    continuity_score: float = Field(ge=0, le=1)
    provenance_score: float = Field(ge=0, le=1)
    dialogue_language_score: float = Field(default=1.0, ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)
    passed: bool
    cliffhanger_options: list[str] = Field(default_factory=list)


class QualityReport(StrictModel):
    input_chapter_count: int = Field(ge=0)
    total_episodes: int = Field(ge=0)
    total_shots: int = Field(ge=0)
    schema_valid: bool
    warnings: list[str] = Field(default_factory=list)
    overall_score: float | None = Field(default=None, ge=0, le=1)
    episode_scores: list[EpisodeQualityScore] = Field(default_factory=list)
    badcases: list[QualityBadcase] = Field(default_factory=list)
    root_causes: list[str] = Field(default_factory=list)
    repair_suggestions: list[str] = Field(default_factory=list)


class ScriptDocument(StrictModel):
    series_metadata: SeriesMetadata
    visual_bible: VisualBible | None = None
    characters: list[Character] = Field(min_length=1)
    episodes: list[Episode] = Field(min_length=1)
    source_map: list[SourceMapEntry] = Field(min_length=1)
    production_notes: list[str] = Field(default_factory=list)
    quality_report: QualityReport | None = None

    @model_validator(mode="after")
    def validate_source_coverage(self) -> "ScriptDocument":
        episode_chapters = {episode.source_chapter_id for episode in self.episodes}
        mapped_chapters = {entry.chapter_id for entry in self.source_map}
        missing = episode_chapters - mapped_chapters
        if missing:
            raise ValueError(
                "source_map must include every episode chapter: "
                + ", ".join(sorted(missing))
            )
        return self


def script_json_schema() -> dict:
    """Return the JSON Schema used in prompts and documentation."""
    return ScriptDocument.model_json_schema()
