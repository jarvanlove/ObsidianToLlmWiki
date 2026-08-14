# M3 Engineering Quality Gates Acceptance

Date: 2026-08-14

Machine-verified baseline: `d1e5d6aa0937e41625656be7e440ce187e361632`

## Acceptance status

M3 machine acceptance passed. Product-owner approval is still required before M4 begins.

## Verified scope

| Task | Verified outcome |
|---|---|
| Task 4 | Deterministic P3-P0 classification returns reasons and source; uncertainty promotes one level; P1/P0 cannot enter implementation without responsibility confirmation. |
| Task 5 | A Bug cannot leave investigation without reproduction or explicit non-reproduction evidence, root cause, minimal-fix rationale, and observable acceptance. Non-Bug work is not forced through a Bug contract. |
| Task 6 | Planned changes continue; scope drift is explained and gated by effective risk; high-risk drift clears prior confirmation; a third distinct failed implementation blocks further blind patches until root cause is rechecked. |
| Task 7 | Schema-v2 receipts require structured evidence; prose-only success, non-zero passing claims, unknown sources, P1/P0 AI-only evidence, and legacy v1 prose receipts fail closed. |

## Disposable integration rehearsal

A disposable project exercised the four gates as one workflow rather than isolated unit tests.

### P2 Bug path

1. A Bug without a root-cause contract was blocked before planning.
2. A complete contract allowed planning and implementation.
3. Changes inside the declared source/test scope continued without drift.
4. Repeating the same failed implementation did not inflate the counter.
5. The third distinct failed implementation blocked the task; a fourth blind patch was rejected.
6. Recording a revised root cause and minimal fix allowed investigation to restart; a passing attempt reset the failure count to zero.

### P1 authentication path

1. Authentication-session work was classified P1 with an explainable deterministic reason.
2. Implementation was blocked until a responsibility owner was recorded.
3. An unplanned production-deployment path triggered `reconfirm`, blocked continuation, and cleared the previous confirmation.
4. AI self-check evidence alone was blocked with `independent_evidence_required`; deterministic passing evidence satisfied the verification gate.

### Evidence compatibility boundaries

- A passing claim with exit code `1` was blocked.
- A prose-only “tests passed” claim was marked `legacy_unstructured` and blocked.
- A schema-v1 resolved receipt was read as schema v2 compatibility data but remained blocked rather than silently closing the task.

### Defect found and repaired during acceptance

The first real PowerShell close attempt exposed a cross-platform timestamp defect: `Get-Date -Format o` emits seven fractional-second digits, while the Python parser accepted at most six. The valid evidence was blocked as `invalid_recorded_at`. A failing regression reproduced the problem; the minimal repair normalizes only excess fractional-second precision before parsing. Malformed timestamps remain blocked. The first patch omitted the standard-library `re` import, was recorded as a failed implementation, and was corrected before the complete acceptance suite was rerun.

## Machine evidence

- M3 targeted risk, diagnosis, scope, evidence, and receipt suites: 35 tests passed.
- `python -m unittest discover -s tests -v`: 174 tests passed in 74.880 seconds after the timestamp repair.
- `python 00_system/scripts/doctor.py --repo-root . --wiki-root C:\Work\note\ObsidianToWiki-private --strict --format json`: passed with trusted context integrity.
- Python compilation for the governance/session/runtime entry modules: passed.
- Governed acceptance scope evaluation: `continue`, no drift, no blocking condition.
- `git diff --check`: passed.

## Known boundaries

- M3 proves engineering quality gates; it does not yet implement the M4 explanation package, human-understanding confirmation, or capability-recovery loop.
- The deterministic risk registry is intentionally conservative and rule-based. New boundary classes must be added as reviewable rules rather than hidden model scores.
- ISO-8601 evidence timestamps retain their original recorded value in the receipt; normalization is used only for validation so provenance is not rewritten.
- A machine pass proves the implemented contracts behave as specified; it does not replace product-owner judgment about interruption level and responsibility boundaries.
- The attached private Wiki still has unmanaged legacy core projections. Automatic memory compilation must continue to refuse forced overwrite until that separate migration is explicitly approved; this does not invalidate the M3 code gates or the explicit project-memory file-back.

## Product-owner checkpoint

Approve M3 only if these behaviors are acceptable:

1. AI must establish a Bug root cause and minimal repair contract before coding.
2. AI must stop when work expands beyond the approved scope instead of silently broadening the patch.
3. Three different failed implementations for the same acceptance condition must force a fresh diagnosis.
4. P1/P0 work needs a named responsibility confirmation before implementation.
5. Verification must be structured and machine-consistent; high-risk closure cannot rely only on the same AI's self-check.

Approval closes M3 and authorizes M4 Tasks 8-9. It does not pre-approve M4 implementation or acceptance.
