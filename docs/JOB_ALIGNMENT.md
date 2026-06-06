# ReelForge YAML 求职岗位匹配说明

这份文档用于把 ReelForge YAML 包装成产品经理实习生项目展示，重点对应岗位要求里的“业务系统定义与设计、0 到 1 落地、产品能力进阶、十倍效能沉淀”。

## 项目一句话

ReelForge YAML 是一个面向小说作者的 AI 辅助改编工作台：把 3 章以上小说转换成可编辑、可校验、可追溯的镜头级 YAML 剧本初稿，并提供质量评测和人机协同修改能力。

## 对应岗位要求

| 岗位要求 | 项目体现 |
| --- | --- |
| 需求分析 | 从“小说作者想改剧本”拆到真实痛点：不会分集分镜、AI 容易编造、普通剧本文字难接视频/TTS/剪辑。 |
| 产品设计 | 设计输入、生成、评测、编辑、导出、展示六段式工作流，让作者先拿到可打磨初稿。 |
| 架构选型 | 使用 JSON-first、Pydantic Schema、YAML 导出、source map、quality report，兼顾模型效率和工程确定性。 |
| 代码实现 | Python + Streamlit 实现章节解析、LLM/OpenAI-compatible 调用、离线 fallback、YAML 校验、评测和展示前端。 |
| 复杂问题解决 | 没有追求不可控的一键成片，而是把高风险视频生成降级为 video-ready storyboard showcase，保证低成本可演示。 |
| 复盘沉淀 | 用 golden benchmark 跟踪 raw/optimized 分数、badcase 数和修复效果，而不是主观评价生成质量。 |
| 自驱探索 | 主动把题目从“写剧本”扩展为“面向内容生产链路的结构化工具”，但保留比赛主线。 |

## 求职展示重点

1. 我不是只接收指令做工具，而是先判断用户真正要什么。
2. 我没有盲目追求全自动成片，因为真实视频 API 成本高、失败率高、并且不是比赛核心。
3. 我把核心交付收敛到可信 YAML 初稿，再用展示页证明它后续可接视频生产。
4. 我用 Schema、provenance、quality report、benchmark 把 AI 输出变成可评估、可复盘的产品系统。

## 可说的技术亮点

- 章节解析：支持 3+ 章小说输入，不足 3 章直接拦截。
- 结构化生成：模型输出 JSON，经过 Pydantic 校验后再导出 YAML。
- 来源追溯：每个镜头保留 `source_ref`，全局保留 `source_map`。
- 质量评测：评估 hook、cliffhanger、power shift、visual executability、continuity、provenance。
- 人机协同：作者可以编辑 YAML，也可以应用局部 cliffhanger 备选，不必整篇重跑。
- 展示前端：无成本 9:16 storyboard preview，适合录屏和面试讲解。

## 简历项目描述草稿

ReelForge YAML｜AI 小说转短剧剧本工作台  
独立完成从需求分析、产品设计到 Python/Streamlit 原型实现：支持 3 章以上小说自动解析，输出可编辑、可校验、可追溯的镜头级 YAML 剧本初稿；设计 Pydantic Schema、source map、quality report 和 human-in-the-loop 编辑流程；构建 golden benchmark，用硬指标评估 hook、cliffhanger、视觉可执行性和来源追溯，证明优化前后 badcase 变化；新增无成本 9:16 storyboard showcase，用于展示后续 AI 视频/TTS/剪辑流水线就绪能力。
