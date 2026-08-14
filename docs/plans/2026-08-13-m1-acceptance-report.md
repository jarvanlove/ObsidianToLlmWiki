# M1 Automatic Memory and Human Product Acceptance

Date: 2026-08-13

Accepted baseline: `cfbd6b8275af3d23bbab1e5b1b64627e6e8f04ea`

## Acceptance decision

The product owner explicitly approved M1 on 2026-08-13. Acceptance continues during normal use of attached projects; this is operational observation, not a reason to keep M1 formally open.

M2 may start only after the current migration/file-back batch closes. Operational findings from M1 must be recorded as defects or follow-up tasks and must not be hidden by M2 implementation.

## Verified scope

| Task | Verified outcome |
|---|---|
| 0C | Resolved, evidence-backed receipts compile into stable, idempotent atomic memory cards with review, supersede, dispute, and sensitive-content boundaries. |
| 0D | Seven current projections stay bounded; empty, normal, and 100KB projects migrate non-destructively with backups, conflict preservation, and restoration evidence. |
| 0E | Natural-language status and the local cockpit consume one evidence-backed projection and passed U2 desktop/mobile/keyboard/privacy acceptance. |
| 0F | Attach/start/continue/close/resolve reuse one task identity; context checks and candidate generation are passive; compilation waits for receipt resolution; maintenance failures remain explicit. |

Final M1 regression: 128 tests passed, strict Doctor passed, and local/remote Git refs matched at the accepted baseline.

## Operational acceptance questions

Normal project work continues to observe four product outcomes:

1. The user does not need to issue Wiki commands for memory maintenance.
2. The system can identify the facts and evidence used for a task.
3. Natural-language status is easier to consume than manually reading the Markdown tree.
4. Damaged, unmigrated, stale, or conflicting Wiki content causes explicit degradation instead of silent overwrite or model guessing.

## Known boundary

The current ObsidianToWiki private project core pages remain manually maintained. Automatic projection compilation therefore reports `pending_memory_repair` until an explicit non-destructive migration is approved. This safety behavior passed; operational migration remains a follow-up and does not invalidate the accepted M1 implementation.
