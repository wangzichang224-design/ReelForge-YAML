# Contest Submission Checklist

This checklist maps the contest rules to concrete repository actions for ReelForge YAML.

## Required Artifacts

- [ ] Public GitHub/Gitee repository after the submission deadline.
- [ ] Runnable source code on `main`.
- [ ] README with product explanation, setup steps, demo flow, dependencies and originality notes.
- [ ] YAML Schema design document: `docs/YAML_SCHEMA.md`.
- [ ] Demo video with voice narration.
- [ ] Demo video link added to README.

## PR / Commit Compliance

- [ ] Do not push future feature work directly to `main`.
- [ ] Create one branch per feature or document update.
- [ ] Open one PR per small feature.
- [ ] Fill every PR description with:
  - title
  - function description
  - implementation idea
  - test method
  - dependency/originality note
- [ ] Keep PR descriptions consistent with actual code changes.
- [ ] Keep all future commit timestamps within the selected contest batch window.
- [ ] Avoid last-day bulk imports.

## Dependency / Originality Compliance

- [ ] All third-party dependencies are listed in `requirements.txt` and `pyproject.toml`.
- [ ] README explains the purpose of each dependency.
- [ ] README lists original implementation modules.
- [ ] References to external open-source projects are clearly labeled as references, not copied code.
- [ ] If any personal historical code is reused later, the PR description states the source and modification scope.

## Demo Video Script

Recommended 3-5 minute structure:

1. State the contest topic: AI novel-to-script tool.
2. Explain the user pain: novel authors need editable first drafts, provenance and lower adaptation cost.
3. Show input: paste or upload a 3-chapter novel.
4. Show generation: structured YAML with metadata, characters, episodes, shots and source map.
5. Show evaluation: hook score, cliffhanger score, power shift, visual executability and badcases.
6. Show human-in-the-loop edit: choose a cliffhanger option or edit YAML.
7. Show export: download YAML and point to `docs/YAML_SCHEMA.md`.

## Final Smoke Test

Run before final submission:

```powershell
python -m pytest
python scripts\evaluate_yaml.py --input samples\deepseek_shadow_contract_3ch_output.yaml
python scripts\evaluate_yaml.py --input samples\deepseek_shadow_contract_3ch_optimized.yaml
python -m streamlit run app.py
```

Expected core evidence:

- Tests pass.
- Raw DeepSeek sample exposes opening-hook badcases.
- Optimized sample keeps 3 episodes and 30 shots.
- Streamlit UI opens with input, generation, evaluation, editor and export tabs.
