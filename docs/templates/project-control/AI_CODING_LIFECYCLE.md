# AI Coding Lifecycle

This project is attached to ObsidianToWiki and uses project control files as the local execution layer.

## Start A Task

Before editing:

1. Read `wiki.context.json`.
2. Read `PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `TASKS.md`, and `TESTING.md`.
3. Read relevant project wiki pages from the context file.
4. Classify the request as a normal task, requirement change, bug fix, release check, or operations incident.
5. State task boundary, risk level, expected touched files, and verification plan.

Optional checklist command from the ObsidianToWiki scaffold:

```powershell
python <obsidiantowiki-root>\00_system\scripts\project_session.py start --repo-root .
```

## Close A Task

Before reporting completion:

1. Inspect the diff.
2. Record exact verification commands and results.
3. Update `TASKS.md`.
4. Check whether `PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `TESTING.md`, `SECURITY.md`, `DEPLOYMENT.md`, `OPERATIONS.md`, `CHANGELOG.md`, or `docs/adr/` should change.
5. File back only durable conclusions to the wiki.

Optional checklist command:

```powershell
python <obsidiantowiki-root>\00_system\scripts\project_session.py close --repo-root . --verification "<commands and result>"
```

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
