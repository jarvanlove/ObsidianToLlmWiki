# Testing

## Commands

PowerShell wrappers:

```powershell
.\00_system\scripts\lint_wiki.ps1
.\00_system\scripts\rebuild_indexes.ps1
.\00_system\scripts\version_status.ps1
```

macOS / Linux wrappers:

```bash
./00_system/scripts/lint_wiki.sh
./00_system/scripts/rebuild_indexes.sh
./00_system/scripts/version_status.sh
./00_system/scripts/project_session.sh check --repo-root . --strict
```

Python scripts can also be run directly when needed:

```powershell
python .\00_system\scripts\lint_wiki.py
python .\00_system\scripts\rebuild_indexes.py
python .\00_system\scripts\version_status.py
```

## Minimum Verification Matrix

| Change type | Required checks |
|---|---|
| Markdown docs only | relevant file read-through; `lint_wiki.ps1` if indexes/schema affected |
| Shared prompt/pattern/index | `lint_wiki.ps1`, verify `30_shared/索引.md` |
| Project attach templates | inspect generated template wording; if possible, test on disposable project |
| AI session protocol/script | run `project_session.py check --strict` and `handle_nl_request.py --request "开始工作"` / `"继续"` / `"收工"` on a disposable attached project |
| AI adapter templates | test disposable attach with `--install-ai-adapters`; verify no private wiki path is written |
| Python script | targeted script run plus `lint_wiki.ps1` |
| Private sync behavior | run against known private vault only after checking changed paths |
| Schema/template change | `lint_wiki.ps1` and inspect affected generated pages |
| Source ingestion pipeline | ingest a disposable `.md` or `.txt`; verify source note, document map, section notes, extracted text, `derived_pages`, and schema |

## Manual Checks

- Confirm Codex instructions do not require reading `CLAUDE.md`.
- Confirm Claude Code instructions do not require reading `AGENTS.md`.
- Confirm public scaffold assets do not include private raw material or secrets.
- Confirm private project memory is updated for durable conclusions.

## Completion Rule

Report exact scripts run and whether they touched public repo, private vault, or both.
