# M2 Recoverable Governance Acceptance

Date: 2026-08-14

Machine-verified baseline: `05b00f62cdcc6abce41ccd994f3ee4839af73fb5`

## Acceptance status

M2 machine acceptance passed, and the product owner explicitly approved M2 on 2026-08-14. M3 is authorized to begin from Task 4.

## Verified scope

| Task | Verified outcome |
|---|---|
| Task 2 | One ignored `.obsidiantowiki/task-state.json` owns schema-v1 engineering task state. Invalid status, missing identity, invalid risk, illegal transition, and partial atomic writes are rejected without corrupting the previous state. |
| Task 3 | Task start captures branch, HEAD, tracked/untracked paths, path fingerprints, and time. Resume separates pre-existing work, task-added paths, and task changes to pre-existing paths. An open task keeps its identity; branch or HEAD conflicts mark it `stale`. |

## Repeatable recovery rehearsal

A disposable Git repository exercised the public `project_session.py` lifecycle:

1. one tracked modification and one untracked file existed before task start;
2. the task created `task.py`;
3. a different task request was submitted before close;
4. an external commit and branch switch changed both HEAD and branch;
5. the repository was checked again.

Observed results:

- original task ID was preserved;
- the different request did not overwrite the open task;
- pre-existing tracked/untracked counts remained `1 / 1`;
- `task.py` was attributed to the active task;
- recovery status became `stale` with `branch_changed` and `head_changed` reasons.

The current ObsidianToWiki worktree also preserved its real baseline: nine pre-existing tracked changes and 32 public legacy untracked files remained separate from M2 task files.

## Machine evidence

- `python -m unittest discover -s tests -v`: 142 tests passed.
- `python 00_system/scripts/doctor.py --repo-root . --strict --format json`: passed.
- Task 2 and Task 3 targeted state/recovery/lifecycle suites: passed.
- Python compilation and `git diff --check`: passed for M2 implementation and this acceptance batch.
- Local and remote feature-branch refs matched at `05b00f6` before this report commit.

## Known boundaries

- Git branch or HEAD changes are conservatively treated as stale because the runtime cannot infer whether an unrecorded commit came from the current agent or another actor. A resolved task receipt safely permits the next task; an unresolved task requires recovery review.
- The nine existing tracked changes and public `investment-research` legacy directory are outside M2 implementation scope and remain uncommitted.
- M2 does not implement risk classification, root-cause gates, scope-drift gates, structured evidence, or human-understanding gates; those belong to M3 and M4.
- M1 operational observation continues independently and does not invalidate this M2 machine result unless it exposes a blocking recovery defect.

## Product-owner checkpoint

Approve M2 only if these product behaviors are acceptable:

1. an unfinished task must not be silently replaced by a new request;
2. task-before work must remain distinguishable from task work;
3. branch or HEAD conflicts must pause automatic continuation as `stale`;
4. local task-state failure must preserve the last complete JSON rather than guessing or resetting.

The product owner explicitly approved these behaviors on 2026-08-14 and authorized M3. This approval closes the M2 checkpoint; it does not pre-approve any M3 implementation or acceptance result.
