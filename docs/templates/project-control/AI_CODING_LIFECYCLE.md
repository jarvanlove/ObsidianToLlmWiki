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

When a UI task has no approved reference design, use the shared visual-direction registry. The runtime selects its fixed fallback rather than random colors; controlled directions require the user's recorded choice, and a project baseline remains locked until an approved U3 RFC changes it.

The agent invokes the lifecycle runtime internally. Do not ask the user to locate the runtime or run a checklist script.

## Close A Task

Before reporting completion:

1. Inspect the diff.
2. Record exact verification commands and results.
3. Update `TASKS.md`.
4. Check whether `PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `TESTING.md`, `SECURITY.md`, `DEPLOYMENT.md`, `OPERATIONS.md`, `CHANGELOG.md`, or `docs/adr/` should change.
5. File back only durable conclusions to the wiki.

For U1+ work, do not close until the linked UI task has passed its visual-evidence gate. A material UI task needs browser screenshots, an independent Visual QA report, and accessibility evidence. U2/U3 additionally require recorded visual-direction approval.

The agent records and resolves the close receipt internally before reporting completion.

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
