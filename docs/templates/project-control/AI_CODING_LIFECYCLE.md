# AI Coding Lifecycle

This project is attached to ObsidianToWiki and uses project control files as the local execution layer.

## Project Cockpit

Daily user-facing commands:

| User says | Agent does |
|---|---|
| `开始工作` | Attach the project if needed, run a strict check, or restore context for an attached project. |
| `继续` | Inspect task state, current diff, wiki binding, and continue the next actionable step. |
| `收工` | Inspect diff and verification, update relevant control files, and produce wiki file-back candidates. |

Users should not need to remember script names, file names, hook names, or subagent names.

## Start A Task

Before editing:

1. Read `wiki.context.json`.
2. Read `PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `TASKS.md`, and `TESTING.md`.
3. Read relevant project wiki pages from the context file.
4. Classify the request as a normal task, requirement change, bug fix, release check, or operations incident.
5. State task boundary, risk level, expected touched files, and verification plan.

## UI Task Gate

For user-facing work, the agent classifies UI impact before implementation:

| Level | Meaning | Gate |
|---|---|---|
| U0 | No UI impact | Normal lifecycle only |
| U1 | Local UI change inside the approved system | Reuse `docs/design/UI_CONTRACT.md`; close with screenshots, Visual QA, and accessibility evidence |
| U2 | New or materially redesigned user flow | Record a UI task and obtain Design Authority direction approval before implementation |
| U3 | Global visual, token, component, or brand-system change | U2 gates plus an approved Design RFC |

The agent owns classification and internal runtime calls. The user does not need to run a script or memorize these levels. A named UI Skill is only an executor; it cannot override approved design sources. For U1+ use the `otw.py ui` runtime to create and validate project-local UI task evidence.

When a UI task has no approved reference design, silently use the shared visual-direction registry's fixed fallback rather than random colors. Do not ask the user to learn palettes or UI levels. If the user says the result feels wrong, first fix local hierarchy/spacing/content problems when that is the real issue; otherwise present exactly three plain-language direction choices and accept a simple reply such as `第二个` or `就这个`. The Agent records the choice internally. A request to change an existing project's overall feel remains a U3 baseline change, but explain it to the user as an overall style adjustment rather than an RFC.

The agent invokes the lifecycle runtime internally. Do not ask the user to locate the runtime or run a checklist script.

## Bug Root-Cause Gate

A bug fix remains `investigating` or becomes `blocked` until the task record contains:

1. reproduction steps or explicit evidence explaining why direct reproduction is unavailable;
2. the root cause, not only the visible symptom;
3. why the proposed change is the smallest sufficient fix; and
4. at least one observable acceptance condition.

Only bug tasks require this root-cause chain. Do not force a feature, refactor, or docs task to pretend it is a bug. The agent records these facts in the governed task state; the user should not need to maintain a separate checklist.

## Close A Task

Before reporting completion:

1. Inspect the diff.
2. Record each verification as structured evidence with `kind`, `command`, `exit_code`, `result`, `recorded_at`, and `source`.
3. Update `TASKS.md`.
4. Check whether `PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `TESTING.md`, `SECURITY.md`, `DEPLOYMENT.md`, `OPERATIONS.md`, `CHANGELOG.md`, or `docs/adr/` should change.
5. File back only durable conclusions to the wiki.

For U1+ work, do not close until the linked UI task has passed its visual-evidence gate. A material UI task needs browser screenshots, an independent Visual QA report, and accessibility evidence. U2/U3 additionally require recorded visual-direction approval.

The agent records and resolves the close receipt internally before reporting completion.

Close receipts use schema v2. Evidence source must be `deterministic`, `ai_self_check`, `independent_ai_review`, or `human_observation`. A prose-only claim such as “tests passed” is retained only as `legacy_unstructured` and cannot close a task; a non-zero exit code cannot be marked passed. P1/P0 work also needs at least one passing source other than `ai_self_check`. Agents should pass repeatable `--evidence` JSON objects or a bounded `--evidence-file`; users still only say `收工`.

## Update Rules

| Event | Required local update | Optional wiki update |
|---|---|---|
| Task started or completed | `TASKS.md` | Project tasks page |
| Requirement changed | `PRODUCT_SPEC.md`, `TASKS.md` | Project decisions page |
| Architecture boundary changed | `ARCHITECTURE.md` or `docs/adr/` | Project architecture/decisions page |
| Test commands changed | `TESTING.md` | Shared/project learning if reusable |
| Deploy changed | `DEPLOYMENT.md` | Project risks/timeline |
| Operations learning | `OPERATIONS.md` | Project risks/timeline |
| Security/trust boundary changed | `SECURITY.md`, `TASKS.md` | Project risks |
| User-visible release change | `CHANGELOG.md` | Project timeline |

Do not write wiki entries for routine code edits without a durable conclusion.
