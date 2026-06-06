# 赛事提交清单

这份清单把赛事要求映射到 ReelForge YAML 仓库里的具体交付动作。

## 必交材料

- [ ] 提交截止后公开 GitHub/Gitee 仓库。
- [ ] `main` 分支上的源码可直接运行。
- [ ] README 包含产品说明、启动步骤、演示流程、依赖和原创说明。
- [ ] YAML Schema 设计文档：`docs/YAML_SCHEMA.md`。
- [ ] 演示视频讲解稿：`docs/DEMO_VIDEO_SCRIPT.md`。
- [ ] PR 交付计划：`docs/PR_DELIVERY_PLAN.md`。
- [ ] 带语音讲解的演示视频。
- [ ] README 已添加演示视频链接。

## PR / Commit 合规

- [ ] 后续功能不要直接推送到 `main`。
- [ ] 每个功能或文档更新单独建分支。
- [ ] 每个小功能对应一个 PR。
- [ ] 每个 PR 描述都填写：
  - 标题
  - 功能说明
  - 实现思路
  - 测试方式
  - 依赖/原创说明
- [ ] PR 描述与实际代码改动保持一致。
- [ ] 后续 commit 时间保持在所选赛事批次窗口内。
- [ ] 避免最后一天批量导入全部代码。

## 依赖与原创合规

- [ ] 所有第三方依赖都列在 `requirements.txt` 和 `pyproject.toml`。
- [ ] README 说明每个依赖的用途。
- [ ] README 列出本仓库原创实现模块。
- [ ] 外部开源项目明确标注为参考，而不是复制代码。
- [ ] 如果后续复用个人历史代码，PR 描述需说明来源和改动范围。

## 演示视频脚本

推荐 3-5 分钟结构：

1. 说明赛事题目：AI 小说转剧本工具。
2. 解释用户痛点：小说作者需要可编辑初稿、来源追溯和更低改编成本。
3. 展示输入：粘贴或上传一段 3 章小说。
4. 展示生成：包含作品信息、角色、分集、镜头和来源映射的结构化 YAML。
5. 展示评测：hook 分、cliffhanger 分、权力翻转、视觉可执行性和 badcases。
6. 展示人机协同编辑：选择 cliffhanger 备选或直接编辑 YAML。
7. 展示导出：下载 YAML，并指出 `docs/YAML_SCHEMA.md`。

## 最终冒烟测试

最终提交前运行：

```powershell
python -m pytest
python scripts\evaluate_yaml.py --input samples\deepseek_shadow_contract_3ch_output.yaml
python scripts\evaluate_yaml.py --input samples\deepseek_shadow_contract_3ch_optimized.yaml
python -m streamlit run app.py
```

预期核心证据：

- 测试通过。
- DeepSeek 原始样例能暴露 opening-hook badcase。
- 优化后样例保持 3 集和 30 个镜头。
- Streamlit UI 能打开输入、生成、评测、编辑和导出标签页。
