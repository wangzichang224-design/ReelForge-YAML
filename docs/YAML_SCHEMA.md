# AI 短剧剧本 YAML Schema 设计说明

## 设计目标

本 Schema 面向“网文改编为竖屏短剧初稿”，输出要同时服务作者编辑、AI 视频生成、TTS 配音和后续自动剪辑。它不是传统影视剧本格式，而是镜头级生产格式。

## 顶层结构

```yaml
series_metadata: {}
visual_bible: {}
characters: []
episodes: []
source_map: []
production_notes: []
quality_report: {}
```

- `series_metadata`：记录作品名、题材、语气、语言、竖屏规格和 schema 版本。
- `visual_bible`：记录全局视觉黑板，包括角色固定外观、主色调、关键场景和核心道具。
- `characters`：记录角色身份、关系、动机、外观一致性提示词和声音设定。
- `episodes`：每章默认改编为 1 集，包含 hook、情绪曲线、cliffhanger 和镜头列表。
- `shots`：每个镜头包含时长、目的、人物、画面轨、声音轨和原文来源。
- `source_map`：把 episode/shot 绑定回原文片段，方便作者追溯和回改。
- `quality_report`：记录输入章节数、总集数、总镜头数、Schema 校验状态、分项评分和 badcase。

## 为什么不用传统剧本格式

传统剧本常写“内景/日/人物动作/对白”，适合真人剧组阅读，但对 AI 视频生成不够直接。短剧和视频模型更需要：

- 景别：特写、中景、全景、插入镜头。
- 运镜：推镜头、手持跟拍、定格推进。
- 画面主体：谁在做什么、站在哪里、表情如何。
- 光影与场景：豪门宴会、雨夜玻璃、董事包厢等可生成元素。
- 竖屏约束：明确 `aspect_ratio: 9:16`。

因此 Schema 以 `shots` 为核心，而不是以传统 scene 为核心。

## 为什么保留 source_map

网文改编最容易出现两个问题：模型编造关键剧情，以及作者无法判断某个镜头来自哪段原文。`source_map` 和 `shot.source_ref` 解决这件事：

- 每个镜头有 `chapter_id`、`chapter_title`、`source_excerpt`。
- 每个 episode 在 `source_map` 中有对应原文片段。
- 作者可以快速确认“这个反转是不是原文已有”。
- 后续可做 claim-source-map、红队评估和人工复核。

## 为什么增加 visual_bible

长文本按章节生成时，角色外观最容易漂移：第 1 集是黑西装，第 3 集可能变成白衬衫或古装。`visual_bible` 是全局记忆黑板，用来固定：

- 角色 `character_id`、姓名和锁定外观特征。
- 服装、年龄段、气质和负面漂移词。
- 主色调、关键地点和核心道具。
- 可直接注入 `video_prompt` 的视觉一致性提示词。

它让后续图生视频、角色参考图和分镜资产管理更容易接入。

## 为什么先 JSON 后 YAML

YAML 对作者友好，但 LLM 直接输出 YAML 时更容易出现缩进、列表和引号错误。项目采用：

1. 模型输出 JSON object。
2. 用 Pydantic 按 Schema 校验。
3. 校验通过后用 PyYAML 导出 YAML。

这样既保留机器校验稳定性，也保留 YAML 的可读性。

## 为什么拆分 visual_track 和 audio_track

当前 AI 短剧流水线通常是分步生产：

- 文生图/图生视频模型读取 `visual_track.video_prompt`。
- TTS 模型读取 `audio_track.dialogue` 和 `tts_emotion`。
- 音效/配乐读取 `sfx` 和 `music`。
- 剪辑工具根据 `duration_seconds` 和 shot 顺序拼接。

音画分离可以避免把台词、音效和画面提示词混在一起，后续接可灵、Runway、即梦、ElevenLabs、ChatTTS、MoviePy 或 FFmpeg 都更清晰。

## 字段说明

### series_metadata

| 字段 | 说明 |
| --- | --- |
| `schema_version` | 当前 Schema 版本，默认 `1.0.0` |
| `title` | 改编项目名 |
| `author` | 原作者，可为空 |
| `source_type` | 默认 `web_novel` |
| `target_format` | 默认 `vertical_short_drama` |
| `genre` | 题材，如都市逆袭、古风权谋 |
| `tone` | 节奏和情绪风格 |
| `language` | 默认 `zh-CN` |
| `aspect_ratio` | 固定 `9:16` |
| `episode_duration_target` | 推荐 `60-120s` |

### characters

每个角色必须有固定外观提示词和声音设定，服务后续角色一致性和配音。

### visual_bible

`visual_bible` 可为空；启用全局视觉黑板后会包含：

| 字段 | 说明 |
| --- | --- |
| `global_style` | 全局画面风格，如都市商战、雨夜玻璃反光、冷感商业影像 |
| `palette` | 主色调 |
| `key_locations` | 高频地点 |
| `key_props` | 关键道具 |
| `characters` | 每个角色的固定视觉资产 |

`visual_bible.characters[]` 包含 `character_id`、`name`、`locked_traits`、`wardrobe`、`visual_prompt` 和 `negative_drift_terms`。

### episodes

每集必须满足：

- `shots` 数量为 10-15。
- 第一镜头 `purpose` 为 `opening_hook`。
- 最后一镜头 `purpose` 为 `cliffhanger`。
- `emotional_curve` 至少包含 3 个节点。

### shots

核心字段：

- `duration_seconds`：每镜头 1-10 秒。
- `purpose`：镜头叙事目的。
- `visual_track.framing`：镜头景别。
- `visual_track.camera_movement`：运镜。
- `visual_track.visual_notes_zh`：给作者看的中文画面说明。
- `visual_track.video_prompt`：给视频模型的英文提示词。
- `audio_track.dialogue`：台词与 TTS 情绪。
- `source_ref`：原文来源。

### quality_report

`quality_report` 是生成后评估结果，不要求模型一次性生成。它包含：

| 字段 | 说明 |
| --- | --- |
| `overall_score` | 0-1 综合质量分 |
| `episode_scores` | 每集分项评分 |
| `badcases` | 失败字段、原因、根因、修改建议和原文片段 |
| `root_causes` | 聚合根因 |
| `repair_suggestions` | 聚合修改建议 |

`episode_scores[]` 会记录 `hook_score`、`cliffhanger_score`、`power_shift_score`、`visual_executability_score`、`continuity_score`、`provenance_score` 和 `cliffhanger_options`。

## 极简片段示例

```yaml
shots:
  - shot_id: ep01_s01
    duration_seconds: 5.0
    purpose: opening_hook
    characters:
      - 沈砚
      - 顾北辰
    visual_track:
      framing: close_up
      camera_movement: fast push-in
      visual_notes_zh: 把当众羞辱提前到开场三秒，镜头贴近主角脸部。
      video_prompt: A tense vertical short drama opening, a young Chinese man is publicly humiliated at a luxury banquet, dramatic lighting, fast push-in camera, photorealistic, 9:16
    audio_track:
      dialogue:
        - speaker: 顾北辰
          text: 你还敢站在这里？
          tts_emotion: 傲慢、压迫
      sfx:
        - 酒杯落地声
      music: 紧张都市短剧鼓点
    source_ref:
      chapter_id: ch001
      chapter_title: 第一章 退婚宴
      source_excerpt: 顾北辰端着酒杯，故意把话说得很响……
```
