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

## Manual Checks

- Confirm Codex instructions do not require reading `CLAUDE.md`.
- Confirm Claude Code instructions do not require reading `AGENTS.md`.
- Confirm public scaffold assets do not include private raw material or secrets.
- Confirm user-facing UI tasks still use natural language, named Skills are recorded as executors, and Figma/Stitch sources are not treated as approved unless the UI task says so.
- Confirm private project memory is updated for durable conclusions.
- Confirm README, quick start, manual, Skill template, installers, manifests, control templates, architecture, operations, deployment, security, changelog, and tests describe the same setup/update contract.

## Completion Rule

Report exact scripts run and whether they touched public repo, private vault, or both.
