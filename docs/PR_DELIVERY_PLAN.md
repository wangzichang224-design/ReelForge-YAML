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
| PR 3 | Add one polished sample walkthrough output | Gives judges a stable artifact to inspect without calling an API | `python scripts\evaluate_yaml.py --input <sample>` |
| PR 4 | UI polish for evaluation tab | Makes the product easier to demonstrate live | Streamlit smoke test |
| PR 5 | Replace README demo video TODO with final video link | Completes final submission artifact | Open README link and verify video is playable |
| PR 6 | Final submission smoke-check | Ensures `main` is runnable before deadline | Full checklist in `docs/SUBMISSION_CHECKLIST.md` |

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
