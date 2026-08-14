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

## Close Flow

Run `project_session.py close` or `otw.py close` with structured evidence. If a P1/P0 understanding gate blocks, show the seven-part package and wait for the user to respond. After a real response, record it with:

```text
otw.py understand --repo-root <repo> --confirmed-by <human> --understood-impact-and-risks --confirmation-source human
```

For P0, also pass `--explicit-authorization`. Then resolve the receipt candidates normally.

Capability-recovery observation and review-card behavior belong to M4 Task 9 and are not defined here.
