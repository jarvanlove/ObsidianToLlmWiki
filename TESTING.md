# Testing

## Commands

PowerShell wrappers:

```powershell
.\00_system\scripts\lint_wiki.ps1
.\00_system\scripts\rebuild_indexes.ps1
.\00_system\scripts\promote_source_section.ps1
.\00_system\scripts\source_promotion_candidates.ps1
.\00_system\scripts\version_status.ps1
.\00_system\scripts\build_retrieval_index.ps1
python -m unittest tests.test_retrieval_core -v
python -m unittest discover -s tests -v
python -m unittest tests.test_runtime_setup tests.test_runtime_update tests.test_project_scaffold_upgrade -v
python .\00_system\scripts\evaluate_retrieval.py --cases .\00_system\registry\retrieval_eval_cases.json
python .\00_system\scripts\sync_private_vault.py --private-root <private-wiki-root> --dry-run --format json
python .\00_system\scripts\doctor.py --wiki-root <private-wiki-root> --strict
python .\00_system\scripts\source_quality.py --source <source-file> --format json
python -m unittest discover -s tests -v
```

macOS / Linux wrappers:

```bash
./00_system/scripts/lint_wiki.sh
./00_system/scripts/rebuild_indexes.sh
./00_system/scripts/promote_source_section.sh
./00_system/scripts/source_promotion_candidates.sh
./00_system/scripts/version_status.sh
./00_system/scripts/project_session.sh check --repo-root . --strict
./00_system/scripts/build_retrieval_index.sh
python3 -m unittest tests.test_retrieval_core -v
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_runtime_setup tests.test_runtime_update tests.test_project_scaffold_upgrade -v
python3 ./00_system/scripts/evaluate_retrieval.py --cases ./00_system/registry/retrieval_eval_cases.json
python3 ./00_system/scripts/doctor.py --wiki-root <private-wiki-root> --strict
python3 ./00_system/scripts/source_quality.py --source <source-file> --format json
```

Python scripts can also be run directly when needed:

```powershell
python .\00_system\scripts\lint_wiki.py
python .\00_system\scripts\rebuild_indexes.py
python .\00_system\scripts\promote_source_section.py
python .\00_system\scripts\source_promotion_candidates.py
python .\00_system\scripts\version_status.py
python .\00_system\scripts\build_retrieval_index.py
```

## Minimum Verification Matrix

| Change type | Required checks |
|---|---|
| Markdown docs only | relevant file read-through; `lint_wiki.ps1` if indexes/schema affected |
| Shared prompt/pattern/index | `lint_wiki.ps1`, verify `30_shared/索引.md` |
| Project attach templates | inspect generated template wording; if possible, test on disposable project |
| AI session protocol/script | run `project_session.py check --strict` and `handle_nl_request.py --request "开始工作"` / `"继续"` / `"收工"` on a disposable attached project |
| Ambient engineering governance | run `tests.test_ambient_governance_trigger tests.test_manager_skill_install tests.test_project_scaffold_upgrade`; verify explanation creates no task, normal changes create/resume one task with one-line P3/P2 output, deployment stops at P1 confirmation, production-data deletion stops at P0 authorization, unattached mutations fail closed, and managed entry updates preserve user content |
| Structured verification evidence | run `tests.test_engineering_governance_evidence tests.test_project_session_receipt`; verify schema-v2 required fields/source allowlist, non-zero exit handling, P1/P0 independent evidence, v1 legacy blocking, and explicit candidate resolution |
| Human understanding gate | run `tests.test_human_understanding_gate`; verify the exact seven fields, safe summaries, P3/P2 low-noise behavior, hash-bound P1 confirmation, P0 authorization, AI-source rejection, and unified-runtime forwarding |
| Capability recovery loop | run `tests.test_capability_recovery_loop tests.test_memory_compiler`; verify five bounded triggers, one intervention per task, three low-noise choices, observable-event allowlisting, secret/path safety, no scoring, P1 understanding ordering, receipt resolution, pending review, and no direct personal/shared write |
| M4 milestone acceptance | run the disposable P2/P1/P0 plus capability-routing rehearsal recorded in `docs/plans/2026-08-14-m4-acceptance-report.md`, then the Task 8–9 targeted suites and full regression; verify AI confirmation rejection, hash invalidation, separate P0 authorization, receipt-before-memory ordering, no direct personal/shared write, strict Doctor, compilation, governed scope, and diff checks |
| UI governance runtime | run `tests.test_ui_governance`; verify U0 creates no design controls, 19 source directions contain exactly six defaults, the fallback baseline is stable, controlled directions require a user note, U2 blocks implementation until direction approval, U3 blocks implementation until RFC approval, and U1+ close requires screenshot/Visual QA/accessibility evidence |
| Natural-language project attach | run `handle_nl_request.py --request "开始工作"` against an existing disposable git repo and an empty disposable wiki root; verify `wiki.context.json`, control files, wiki core pages, runtime templates, and `page_schemas.json` exist |
| AI adapter templates | test disposable attach with `--install-ai-adapters`; verify no private wiki path is written |
| Python script | targeted script run plus `lint_wiki.ps1` |
| Private sync behavior | run against known private vault only after checking changed paths |
| Schema/template change | `lint_wiki.ps1` and inspect affected generated pages |
| Source ingestion pipeline | ingest a disposable `.md` or `.txt`; verify source note, document map, section notes, extracted text, `derived_pages`, section quality headings, excerpt limits, routing candidates, promotion candidate report, and schema |
| Source extraction quality | run `tests.test_source_ingestion_quality`; verify pass/review/blocked gates, OCR detection, DOCX fallback, CJK normalization, TOC grouping, chapter false-positive rejection, continuation labels, safe reingestion cleanup, map-first ordering, complete refs, and exact excerpt limits |
| Wiki governance semantics | run `tests.test_wiki_governance`; verify sibling/nearest link resolution, fenced-code exclusion, generated/archive boundaries, reviewed-date freshness, domain validation, and product-guide schema exemptions |
| Compatibility/migration | run vault, adapter, shared-asset, project-scaffold, and historical-upgrade tests; verify old Markdown hashes, idempotency, `.new` conflict candidates, explicit `merged`/`keep-local` resolution, and automatic reopening after either hash changes |
| Global manager/runtime | run manager install and lifecycle E2E tests; verify natural-language attach, local path isolation, opt-in adapters, close receipt, and resolution |
| Setup/update lifecycle | run runtime setup/update, private-vault setup, private-sync, and project-scaffold tests; verify nonexistent vault creation, provider isolation, dirty Git rejection, fast-forward detection, baseline-safe updates, conflict backup, and no project reattachment |
| Cross-platform release | GitHub Actions must pass Python 3.10/3.12 on Windows, macOS, and Linux; local platform wrapper smoke test must pass |
| Source section promotion | promote one disposable section note with `promote_source_section.py`; verify formal page, source section backlink, `source_refs`, `promoted_to`, and section status |
| Retrieval core | run `python -m unittest tests.test_retrieval_core -v`; verify incremental update/delete refresh, project/type filters, source refs, JSON schema, and context budget |
| Retrieval quality gate | run `evaluate_retrieval.py`; require gate pass rate `1.0`, MRR at least `0.8`, and review semantic probe recommendation |
| Private sync safety | run `tests.test_private_sync`; verify protected files never appear in real-vault dry-run actions |
| Agent adapters | run `tests.test_agent_retrieval_adapter`; verify MCP initialize, tools/list, structured search, and bounded context calls |
| Provenance migration | run `tests.test_provenance_migration`; verify audit-only default, explicit evidence extraction, no fake page refs, and idempotency |
| Context integrity | run `tests.test_context_integrity`; verify malformed frontmatter, schema errors, stale pages, missing provenance, conflicts, privacy exclusions, and quarantined pages fail or degrade without modifying the wiki |
| Context contract/receipt | run `tests.test_context_contract` and retrieval core; verify L0-L3 precedence, six-card/default 6000-token bounds, deterministic hashes, explicit missing facts, and no quarantined result enters context |
| Memory compiler/projection | run `tests.test_memory_compiler tests.test_memory_projection`; verify resolved-receipt input, stable IDs, idempotency, supersede/dispute rules, page budgets, archives, and evidence backlinks |
| Historical memory migration | run `tests.test_memory_migration`; verify dry-run, backup/manifest, empty-template bootstrap, 100KB fixture migration, restoration, and preservation of user customization |
| Human project cockpit | run `tests.test_project_cockpit tests.test_project_concierge` plus U2 visual close; verify five default areas, progressive disclosure, no secret/absolute-path leak, responsive screenshots, keyboard access, and Context Receipt citations |
| Automatic memory lifecycle | run `tests.test_automatic_memory_lifecycle tests.test_project_lifecycle_e2e`; verify attach/start/continue/close/resolve/compile/projection/cockpit use one task ID and do not require explicit wiki commands |

## Manual Checks

- Confirm Codex instructions do not require reading `CLAUDE.md`.
- Confirm Claude Code instructions do not require reading `AGENTS.md`.
- Confirm public scaffold assets do not include private raw material or secrets.
- Confirm user-facing UI tasks still use natural language, named Skills are recorded as executors, and Figma/Stitch sources are not treated as approved unless the UI task says so.
- Confirm private project memory is updated for durable conclusions.
- Confirm an ordinary user can answer current state, recent changes, open risks, pending decisions, and next step without opening Markdown.
- Confirm default AI context does not include all project control files, all core wiki pages, or superseded/resolved history.
- Confirm damaged or missing wiki context cannot be silently replaced by model inference.
- Confirm README, quick start, manual, Skill template, installers, manifests, control templates, architecture, operations, deployment, security, changelog, and tests describe the same setup/update contract.

## Completion Rule

Report exact scripts run and whether they touched public repo, private vault, or both.

For Human-Controlled AI Engineering 2.0, each milestone additionally records Context Receipt coverage, projection token budgets, compatibility results, and whether a human approval gate was required. A later milestone cannot hide a failed earlier gate.
