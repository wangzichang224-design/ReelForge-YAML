# ReelForge YAML Evaluation Loop

## Why Evaluation Matters

结构 Schema 只能证明模型输出“像一个 YAML 剧本”，不能证明它适合竖屏短剧生产。ReelForge 因此增加了硬指标测评：先发现 badcase，再把 badcase 反馈给 Critic-Generator loop 做局部重写。

这套评测优先覆盖两个比赛展示里最容易被问到的问题：

- 短剧网感：开场是否足够快，结尾是否能骗用户点下一集，集内是否发生权力翻转。
- AI 视频适配：`video_prompt` 是否能被摄影机和视频模型执行，角色外观是否跨集稳定。

## Golden Dataset

`samples/golden_dataset.yaml` 定义当前回归靶子：

- `shadow_contract`：都市商战、证据反转、打脸高潮，用来测试黄金三秒、权力翻转和 cliffhanger。
- `quiet_transition`：办公室沉默、内心独白、低冲突过渡，用来测试戏剧化改写和视觉转译能力。
- `palace_lantern`：古风权谋、宫灯纵火、军械库暗账，用来测试非现代题材的视觉黑板和证据反转。
- `hospital_will`：医疗家庭、遗嘱逼签、电子签名，用来测试强情绪冲突、道具证据和身份曝光钩子。
- `midnight_refund`：客服职场、退款异常、仓库监控，用来测试低冲突文本的屏幕信息和动作可视化。

每个样例都保存 expected targets，而不是只保存输入文本。这样每次改 prompt 或改 pipeline 都可以对同一批硬指标做对比。

## Metrics

`src/shortdrama_yaml/evaluator.py` 计算以下指标：

- `hook_score`：首镜头是否直接出现冲突、羞辱、逼问、证据、阻拦、言语压迫或具体对抗动作。
- `cliffhanger_score`：尾镜头是否卡在真相、危机、身份暴露、证据揭晓或反派反扑之前。
- `power_shift_score`：每集是否存在 reversal/payoff，且情绪曲线里有反转、打脸、揭露或失控。
- `visual_executability_score`：英文 `video_prompt` 是否包含 shot type、camera movement、concrete action、lighting、vertical 9:16，并拒绝抽象文学词。
- `continuity_score`：同一角色是否继承 `visual_bible` 的固定外观提示，避免跨集服装/年龄/气质漂移。
- `provenance_score`：`source_ref` 是否是真实原文片段；标记“原文未直接描述/改编自情境”的镜头会进入 badcase。

## Critic-Generator Protocol

生成链路支持两个开关：

- `enable_scratchpad`：先构建 `visual_bible`，提取角色固定外观、场景、主色调和关键道具，再注入镜头提示词。
- `enable_critic_loop`：先评测，再对失败的 episode/shot 做最多 2 轮局部重写。

局部重写不会整篇重跑，避免成本失控和剧情漂移。当前规则会重点修复：

- 假 opening hook：把前 6 个镜头里冲突最强的镜头提前，或改成黄金三秒对峙。
- 弱 video prompt：补足 shot type、主体动作、道具、光影、vertical 9:16。
- 角色漂移：把 `visual_bible` 中的固定角色提示注入相关镜头。

## Checked-In Badcase Result

原始 DeepSeek 样例：

```powershell
python scripts\evaluate_yaml.py --input samples\deepseek_shadow_contract_3ch_output.yaml
```

结果：

- overall_score = 0.811
- episodes = 3
- shots = 30
- badcases = 14
- hook_score = 0.20 / 0.40 / 0.55

根因：3 集首镜头都被标为 `opening_hook`，但画面仍偏雨夜、车库、会议室铺垫，没有在前 3 秒制造直接对峙。

优化命令：

```powershell
python scripts\evaluate_yaml.py `
  --input samples\deepseek_shadow_contract_3ch_output.yaml `
  --scratchpad `
  --optimize `
  --output samples\deepseek_shadow_contract_3ch_optimized.yaml
```

优化后：

- overall_score = 0.95
- episodes = 3
- shots = 30
- hook_score = 1.00 / 1.00 / 1.00
- cliffhanger_score = 0.85 / 0.85 / 0.85
- power_shift_score = 1.00 / 1.00 / 1.00
- visual_executability_score = 0.95 / 0.95 / 0.95
- continuity_score = 1.00 / 1.00 / 1.00
- remaining badcases = 3 provenance notes

剩余 provenance notes 是有意保留的：这些镜头的 `source_ref` 明确写着“改编自情境”，系统不应伪造原文来源。它们会提示作者回改或确认改编合理性。

## Human-In-The-Loop UI

Streamlit 的“测评与优化”区会展示：

- 总分、badcase 数、集数、镜头数。
- 每集分项表格。
- badcase 的失败字段、根因、修改建议和原文片段。
- 每集 3 个 cliffhanger 备选：身份曝光型、危机降临型、反派反扑型。

用户选择某个 cliffhanger 备选后，只改对应集的尾镜头和 `quality_report`，不会重写整篇剧本。
