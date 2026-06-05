# PR Delivery Plan

The contest rules require continuous delivery through focused Pull Requests. This plan keeps future work small, auditable and easy to merge.

## Current Baseline

- `main` is runnable.
- PR #1 established submission compliance docs and PR template.
- Future changes should not be pushed directly to `main`.

## Recommended PR Sequence

| PR | Scope | Why It Matters | Validation |
| --- | --- | --- | --- |
| PR 2 | Add demo video script and README link guidance | Prepares the required narrated demo video | `python -m pytest` |
| PR 3 | Add three golden evaluation novels | Expands benchmark coverage beyond one urban-business sample | `python -m pytest` plus chapter parsing checks |
| PR 4 | Add golden benchmark runner and report | Makes quality changes measurable across samples | `python scripts\run_golden_benchmark.py` |
| PR 5 | Improve evaluator metrics | Catches genre drift, non-Chinese dialogue and weak prompt grammar | `python -m pytest` |
| PR 6 | Improve prompts and critic loop | Turns measured badcases into local rewrites | Benchmark raw vs optimized comparison |
| PR 7 | Add benchmark evidence to demo docs | Gives judges a concise before/after narrative | README and demo script review |

## PR Rules

- One PR should change one feature, document or test scope.
- Every PR description must use `.github/pull_request_template.md`.
- PR descriptions must not be blank.
- Implementation notes must mention any external dependency or reused code.
- Every merged PR should leave `main` runnable.

## Commit Rules

- Use concise commit messages that describe the actual change.
- Keep all future commit timestamps within the selected contest batch window.
- Avoid bulk imports.
- Do not rewrite published history unless there is a serious security issue.

## Known Compliance Risk

Earlier setup work was committed directly to `main` before the PR workflow was established. Do not try to fake historical PRs. Instead, keep the remaining development auditable through real PRs with accurate descriptions.
