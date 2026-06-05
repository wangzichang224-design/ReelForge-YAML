# Demo Video Script

Use this as the narration and screen-flow script for the required contest demo video.

## Target Length

3-5 minutes.

## Video Goal

Show that ReelForge YAML satisfies the contest topic: it converts 3+ chapters of novel text into an editable YAML script draft, with a documented Schema and a product rationale for reducing authors' adaptation cost.

## Recording Checklist

- [ ] Use voice narration.
- [ ] Show the repository README.
- [ ] Show the Streamlit app running locally.
- [ ] Show a 3-chapter novel input.
- [ ] Show generated YAML.
- [ ] Show `docs/YAML_SCHEMA.md`.
- [ ] Show quality evaluation and badcase optimization.
- [ ] Show YAML export.
- [ ] Upload to a public video or cloud platform.
- [ ] Replace the README `TODO` demo link with the real URL.

## Narration Script

### 1. Opening: Contest Topic And User Pain

大家好，我的作品是 ReelForge YAML，对应题目三：AI 小说转剧本工具。

这个题目的核心用户是小说作者。他们有完整的故事和章节文本，但把小说改成剧本会遇到几个问题：不熟悉剧本结构，不会拆分镜头，AI 直接生成又容易编造剧情，而且普通剧本文字也很难继续接 AI 视频、TTS 和剪辑工具。

所以我没有只做一个“让大模型写剧本”的工具，而是做成一个面向创作者工作流的 AI 辅助改编产品：把 3 章以上小说转换成可编辑、可校验、可追溯的 YAML 剧本初稿。

### 2. README: Product Positioning

这里是项目 README。可以看到我把赛事题目、用户痛点、需求映射和设计原因写在最前面。

我把场景进一步收敛到网文转竖屏短剧，因为网文作者当前更常见的商业化方向是短剧改编。短剧对开场 hook、集内反转、结尾钩子和镜头级画面要求更高，也更需要结构化数据。

### 3. App Input: Three-Chapter Novel

现在打开 Streamlit demo。左侧是生成配置，可以选择离线 demo 或配置 DeepSeek / OpenAI-compatible API。

在输入区，我粘贴或上传一段至少 3 章的小说文本。系统会自动识别章节边界，如果少于 3 章会直接提示不符合题目要求。

### 4. Generate YAML

点击生成后，系统会完成章节解析、剧情抽取、短剧改编、镜头生成、Schema 校验和 YAML 导出。

生成结果不是普通自然语言，而是结构化 YAML。它包含：

- `series_metadata`：作品信息和竖屏规格。
- `visual_bible`：角色固定外观和视觉资产。
- `characters`：角色关系、动机、声音和外观提示词。
- `episodes`：每章默认改成一集。
- `shots`：每集 10-15 个镜头，有景别、运镜、画面提示词、台词、音效和来源引用。
- `source_map`：每集和镜头对应的原文片段。

### 5. Schema Document

这里是 `docs/YAML_SCHEMA.md`。文档解释了为什么不用传统剧本格式，而要用镜头级 YAML。

原因是 AI 视频和短剧生产更需要镜头、景别、运镜、音画分离和来源追溯。YAML 对作者可读，但模型直接输出 YAML 不稳定，所以系统采用 JSON-first：先让模型输出 JSON，再通过 Pydantic 校验，最后导出 YAML。

### 6. Evaluation And Badcase Optimization

接下来展示“测评与优化”区。

单纯 Schema valid 只能证明格式对，不代表短剧效果好。所以我增加了硬指标评测：

- opening hook 是否真的在前 3 秒制造冲突。
- cliffhanger 是否能激发下一集观看欲。
- power shift 是否有权力翻转。
- video prompt 是否可被 AI 视频模型执行。
- 角色视觉是否跨集一致。
- source_ref 是否来自原文。

这里我重点展示 `reports/golden_benchmark.md`。我没有只跑一个样例，而是构建了 5 个 golden samples：都市商战、平淡办公室、古风权谋、医疗遗嘱、客服职场悬疑。

当前 benchmark 的 raw average score 是 0.905，但 raw badcases 有 75 个，主要集中在视觉可执行性：有些画面说明还停留在文学表达，没有完整的 shot type、动作、场景、运镜和光影。

经过 visual scratchpad 和 critic loop 后，系统只局部重写不合格镜头，不整篇重跑。优化后 average score 提升到 0.944，optimized badcases 从 75 降到 0，badcase reduction rate 是 1.0。

这就是这个项目的迭代闭环：不是主观说“效果更好了”，而是用 golden dataset 和硬指标证明每次优化到底解决了哪些 badcase。

### 7. Human-In-The-Loop Editing

这个工具不是替作者做最终决定，而是让作者更快拿到可打磨初稿。

用户可以在 YAML 编辑器里直接修改，也可以在测评区选择 cliffhanger 备选，例如身份曝光型、危机降临型、反派反扑型。选择后系统只改对应集的尾镜头，避免整篇重写导致剧情漂移。

### 8. Export And Closing

最后可以下载 YAML 剧本、Schema 文档和样例输出。

这个项目的意义是降低小说作者进入剧本改编的门槛，把 AI 从“不可控代写”变成“可信任的结构化辅助工具”。它既能快速生成初稿，也保留来源、质量评测和人工修改空间，为后续 AI 视频、TTS 和剪辑流水线打基础。

谢谢观看。
