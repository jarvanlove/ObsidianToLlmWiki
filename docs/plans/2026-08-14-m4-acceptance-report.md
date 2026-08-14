# M4 Human Understanding and Capability Recovery Acceptance

Date: 2026-08-14

Machine-verified baseline: `4f03af9e359321ad06fc10460ab48e206938d7b3`

## Acceptance status

M4 machine acceptance passed, and the product owner explicitly approved M4 on 2026-08-14. M5 is authorized to begin from Task 10.

## Verified scope

| Task | Verified outcome |
|---|---|
| Task 8 | Every close receipt contains the exact seven-part safe explanation package. P3 auto-passes, P2 displays without confirmation, P1 requires current hash-bound human understanding, and P0 additionally requires explicit authorization. AI-originated confirmation is rejected. |
| Task 9 | Capability intervention stays quiet without evidence, uses only five trigger classes, offers exactly three choices at most once per task, records only allowlisted observable events, exposes no aggregate score, and cannot write directly to personal or shared memory. |

## Disposable integration rehearsal

A disposable workspace exercised the M4 contracts as one workflow rather than relying only on isolated unit tests.

### Explanation and understanding path

1. A P2 change produced all seven explanation fields and passed with the non-blocking `display` action.
2. A P1 authentication change was blocked before human confirmation.
3. An AI self-check was rejected as a human confirmation source.
4. A named human confirmation passed only for the current explanation package.
5. Changing the package invalidated the old confirmation and blocked the P1 gate again.
6. A P0 production-deletion scenario remained blocked after understanding confirmation alone and passed only after separate explicit authorization.

### Capability-recovery path

1. No signal produced no intervention.
2. New concept, P1/P0 risk, repeated same-module issue, AI misjudgment, and consecutive understanding skips each triggered the same exact three choices.
3. A second trigger in the same task reused the first intervention instead of interrupting again.
4. A receipt-backed observable root-cause event produced one pending personal-memory suggestion without a score.
5. Direct shared routing was rejected.
6. Memory compilation was blocked before receipt resolution.
7. After resolution, the candidate compiled only as `pending_review`; no `10_personal` or `30_shared` directory was written directly.

## Machine evidence

- Disposable M4 integration rehearsal: passed.
- `python -m unittest tests.test_human_understanding_gate tests.test_capability_recovery_loop -v`: 13 tests passed.
- `python -m unittest discover -s tests -v`: 187 tests passed in 52.403 seconds.
- `python 00_system/scripts/otw.py doctor --strict`: passed with trusted context integrity.
- Python compilation for `engineering_governance.py`, `project_session.py`, and `memory_compiler.py`: passed.
- Governed acceptance scope evaluation: no unplanned path or blocking drift.
- Public and private file-back diffs: whitespace checks passed.

## Defect result

The independent rehearsal found no new Task 8 or Task 9 implementation defect. No production code was changed during acceptance.

The first real close attempt used JavaScript-style UTC timestamps ending in `Z`; the schema-v2 evidence validator rejected all four records as `invalid_recorded_at`, so the receipt correctly remained blocked and the failed attempt was not counted as acceptance. Reissuing the same evidence with the runtime's explicit-offset ISO format passed. UTC `Z` compatibility is therefore an explicit M5 compatibility follow-up, not a hidden M4 pass or an in-scope M4 repair.

## Known boundaries

- M4 proves the explanation, understanding, authorization, and evidence-routing contracts. It does not prove that a person has recovered all traditional coding ability.
- M4 does not activate governance from ordinary natural-language coding requests. That behavior belongs to M5 Task 10 and remains unimplemented.
- The current evidence timestamp validator accepts explicit-offset timestamps emitted by the runtime but rejects JavaScript-style UTC `Z`; M5 compatibility work must decide and test the intended cross-client contract.
- Capability observations require real user behavior. The acceptance harness used disposable synthetic evidence only to verify the mechanism; it did not create a real personal capability record.
- The attached private Wiki still has unmanaged legacy core projections. Automatic memory compilation must continue to refuse forced overwrite until migration is explicitly approved; explicit project-memory file-back remains available.
- Machine acceptance does not replace product-owner judgment about whether interruption frequency and the three choices are acceptable in real use.

## Product-owner checkpoint

Approve M4 only if these behaviors are acceptable:

1. P1/P0 work cannot close on AI self-confirmation; a human must confirm the current explanation package.
2. P0 still needs explicit authorization after the human-understanding confirmation.
3. Explanation changes invalidate earlier confirmation instead of silently carrying it forward.
4. Learning intervention occurs at most once per task and always offers the same three low-noise choices.
5. Capability records remain evidence-backed, reviewable, private by default, and never become an AI-generated score or direct shared write.

The product owner explicitly approved these behaviors on 2026-08-14 and authorized M5. This closes the M4 checkpoint; it does not pre-approve Task 10, Task 11, Task 12, or the final 2.0 release.
