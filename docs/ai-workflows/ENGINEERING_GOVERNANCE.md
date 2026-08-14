# Human Understanding Gate

The user does not maintain this file during normal work. The Agent generates the explanation package from governed task state, project-relative Git changes, scope checks, and structured verification evidence.

Every new close receipt contains exactly seven explanation fields:

1. What changed
2. Why it changed
3. Data or call-chain changes
4. Affected files and boundaries
5. Verification
6. Remaining risks
7. Rollback

Missing facts are reported as `unknown`. The package must not contain source code, secret values, commands that expose credentials, or private absolute paths.

## Risk Behavior

| Risk | Required behavior |
|---|---|
| P3 | Pass automatically and keep the package in the receipt |
| P2 | Show the package and continue without a confirmation ritual |
| P1 | Require a named human to confirm understanding of impact and remaining risk |
| P0 | Require the P1 confirmation plus explicit authorization |

P1/P0 confirmation is bound to the current risk and explanation-package hash. A material package or risk change invalidates the previous confirmation.

The Agent may generate and explain the package, but it must never create a human confirmation. AI review, tool output, silence, or a generic request to continue are not human confirmation. P0 understanding is not authorization.

## Ordinary Requests

The Agent classifies every ordinary request before acting:

| Intent | Governance behavior |
|---|---|
| `read_only` | Inspect and answer without creating a task. |
| `code_change` | Start or resume a governed task before editing. |
| `external_mutation` | Start or resume a governed task before changing external state. |
| `destructive` | Start governance and require the applicable P1/P0 confirmation before acting. |

P3/P2 work stays ambient and uses one concise status line. The Agent interrupts only for an unknown root cause, scope drift, P1/P0 confirmation, insufficient evidence, or a required understanding gate. Ambient governance uses the public runtime and does not depend on a background daemon.

## Close Flow

Run `project_session.py close` or `otw.py close` with structured evidence. If a P1/P0 understanding gate blocks, show the seven-part package and wait for the user to respond. After a real response, record it with:

```text
otw.py understand --repo-root <repo> --confirmed-by <human> --understood-impact-and-risks --confirmation-source human
```

For P0, also pass `--explicit-authorization`. Then resolve the receipt candidates normally.

## Capability Recovery

Capability recovery is optional learning support, not a score or release gate. Offer one lightweight intervention per task only when at least one observable signal exists: a new concept, P1/P0 risk, a repeated issue in the same module, an AI misjudgment, or consecutive skipped understanding opportunities.

Offer exactly three choices:

1. Let me judge the root cause first.
2. Explain the call chain.
3. Skip learning this time.

Record only auditable events such as identifying a root cause, call chain, risk boundary, rollback point, scope expansion, or verification gap. Never record a comprehensive ability score, personality judgment, source code, secret, or private absolute path.

Capability observations are pending knowledge candidates. They appear in a close receipt only after verification and human-understanding gates pass, then wait for the existing receipt resolution and memory compiler. The default suggested destination is personal memory; project memory is allowed when explicitly justified. Capability observations never route directly to shared memory, and no candidate writes directly to a core Wiki page.

The Agent invokes capability-recovery events through the deterministic governance interface when an observable trigger or event occurs.
