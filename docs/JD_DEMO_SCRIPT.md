# ReelForge YAML 求职展示脚本

目标场景：发给产品经理实习岗位面试官，或录 90-120 秒项目展示视频。

## 90-120 秒版本

大家好，我想用 ReelForge YAML 这个项目展示我对产品经理实习岗位的理解。

我没有把题目简单理解成“让大模型写一段剧本”，而是先做需求分析：小说作者真正缺的不是一段不可控文本，而是一份可编辑、可追溯、可继续打磨的剧本初稿。围绕这个需求，我把产品目标定义为：把 3 章以上小说转换成结构化 YAML，让作者能看到分集、镜头、台词、音效、来源引用和质量提示。

在产品设计上，系统从章节解析开始，把小说拆成 episodes 和 shots。每个镜头都拆成 visual_track、audio_track 和 source_ref：visual_track 面向后续 AI 视频或分镜制作，audio_track 面向台词和声音，source_ref 用来降低 AI 编造剧情的风险。

在架构选型上，我采用 JSON-first 到 YAML 的链路：先让模型输出更容易校验的 JSON，再用 Pydantic Schema 做结构约束，最后导出作者更容易编辑的 YAML。这样既保留 AI 效率，也保留工程上的确定性和可维护性。

在代码实现上，我用 Python 和 Streamlit 做了完整闭环，包括章节解析、离线 demo fallback、OpenAI-compatible 调用、Schema 校验、YAML 编辑器、质量评测和 critic loop。展示页里的 9:16 预览不真正消耗视频生成额度，而是证明每个镜头已经具备视频生产所需的信息结构。

在复盘沉淀上，我没有只凭主观感受说效果变好，而是做了 golden benchmark。项目可以记录 raw/optimized 分数、badcase 数量和修复结果。这对应岗位要求里的复盘沉淀和十倍效率方法论：用数据发现问题，用结构化方案修复问题。

所以这个项目覆盖了需求分析、产品设计、架构选型、代码实现和复盘沉淀。它体现的是我从 0 到 1 推动一个 AI 产品落地的能力，而不是只接收指令写一个工具。

## 录屏顺序

1. 打开 README，停留在项目定位和“视频生产就绪展示”。
2. 打开 Streamlit，展示输入区：3 章小说和章节识别。
3. 展示生成区：YAML 初稿、episodes、shots、source_map。
4. 展示测评区：overall score、badcases、episode scores。
5. 展示项目展示 / 视频预览：9:16 手机预览、镜头时间线、source excerpt、video_prompt。
6. 展示求职展示讲解稿文本区域，说明这是为岗位沟通准备的产品化表达。

## 30 秒压缩版

ReelForge YAML 是我做的 AI 小说转短剧剧本工作台。它不是简单让大模型写剧本，而是先解决小说作者改编门槛高、AI 容易编造、结果难以继续生产的问题。系统把 3 章以上小说解析成 episodes 和 shots，用 JSON-first、Pydantic Schema、YAML 导出保证结构稳定，并用 source map 保留来源追溯。前端支持生成、评测、编辑、导出和 9:16 storyboard 展示。这个项目体现了我从需求分析、产品设计、架构选型到代码实现和复盘沉淀的完整 0 到 1 能力。
