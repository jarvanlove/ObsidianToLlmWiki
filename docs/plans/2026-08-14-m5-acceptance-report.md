# M5 Human-Controlled AI Engineering System 2.0 Acceptance Report

Date: 2026-08-14

Branch: `feature/human-controlled-ai-engineering-v2`

Runtime: `2.0.0` (`stable`)
Project scaffold: v4

## Outcome

M5 Tasks 10–12 are machine-accepted. Ordinary requests can enter governance without requiring the user to remember a command; the system stops only at a real root-cause, scope, risk, or human-understanding boundary. Stable `2.0.0` was selected only after all three disposable pilots passed.

Product-owner approval of M5 remains an explicit checkpoint and is not inferred from machine acceptance.

## A-J Acceptance

| Scenario | Verified outcome |
|---|---|
| A. Normal repair | A normal repair request starts the single governed task without requiring `开始工作`. |
| B. Scope expansion | An unplanned authentication file in an export repair is classified as drift and blocks for replanning. |
| C. Unknown root cause | A Bug cannot leave investigation while `root_cause`, minimal fix, or acceptance is missing. |
| D. P1 login | A simulated authentication change remains blocked until a named human confirms the seven-part explanation package. |
| E. Capability recovery | The observable capability candidate remains personal, pending, evidence-linked, and cannot route directly to shared memory. |
| F. Interrupted work | The Git baseline separates pre-existing user edits from task changes and preserves both. |
| G. Empty project | Local controls produce review-required initial atomic cards without inventing active facts. |
| H. 100KB legacy memory | Migration creates byte-backed manifests, review-required atomic cards, and bounded projections without overwriting the originals silently. |
| I. Damaged Wiki | Broken content is quarantined and excluded instead of being treated as empty or trusted context. |
| J. Passive human UI | Natural-language status and the local cockpit remain available without opening Obsidian. |

Boundary checks also passed: read-only work creates no task; an unattached mutation fails closed and reports that governance coverage is absent.

## Disposable Pilots

| Pilot | Command | Result | Preserved local evidence |
|---|---|---|---|
| Clean new project | `python -m unittest tests.test_project_lifecycle_e2e.ProjectLifecycleE2ETests.test_natural_language_lifecycle_bootstraps_and_closes_disposable_project -v` | Pass | Local session receipt and task identity in the disposable repository |
| Existing uncommitted work | `python -m unittest tests.test_human_controlled_ai_e2e.HumanControlledAiE2ETests.test_f_interrupted_task_preserves_preexisting_changes -v` | Pass | Sanitized pilot summary with pre-existing/task path attribution |
| P1 authentication boundary | `python -m unittest tests.test_human_controlled_ai_e2e.HumanControlledAiE2ETests.test_d_e_p1_requires_human_understanding_and_capability_stays_personal -v` | Pass | Sanitized risk, understanding, and personal-destination summary |

All pilots use temporary local Git projects. Their directories are removed after each test. No production service, credential, private source, or unrelated business repository is used.

## Verification Evidence

- A-J plus project lifecycle: 8 tests passed.
- Stable release and compatibility target: 14 tests passed.
- Final full regression: 205 tests passed in 97.457 seconds.
- Strict Doctor: passed; runtime `2.0.0`, private scaffold v1, project scaffold v4, and trusted context reported.
- Project session strict check: passed with no missing controls and no stale task baseline.
- Memory compiler dry-run: passed; seven current projections reported `would_write` with zero active cards.
- Task scope: no drift; effective risk P2; action `continue`.
- `git diff --check`: passed.

## Remaining Boundaries

- Git remains the code authority; the private Wiki records durable rationale and evidence, not a second code copy.
- Human confirmation is a governance record, not an operating-system permission boundary. Production authorization still depends on the real deployment platform.
- The current attached project has zero active atomic memory cards; compiler dry-run is valid, but existing manually maintained core pages should only be migrated through the explicit backup/manifest workflow.
- M5 is ready for product-owner review. Do not merge the feature branch to `main` until the user approves the large-version iteration.
