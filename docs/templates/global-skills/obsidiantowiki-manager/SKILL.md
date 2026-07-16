---
name: obsidiantowiki-manager
description: Operate ObsidianToWiki from natural language for project attach, daily sessions, retrieval, ingestion, and safe upgrades.
---

# ObsidianToWiki Manager

Use this Skill when the user mentions ObsidianToWiki, project wiki attachment, knowledge ingestion, wiki retrieval, or says `开始工作`, `继续`, or `收工` in a coding project.

## Runtime

- Public runtime root: `{{source_root}}`
- Unified entrypoint: `{{source_root}}/00_system/scripts/otw.py`
- Stable wrappers: `{{source_root}}/00_system/scripts/otw.ps1` and `{{source_root}}/00_system/scripts/otw.sh`.
- Use the platform wrapper so the managed `{{source_root}}/.venv` interpreter is preferred. Resolve the current project repository before invoking it.

## User Experience

- The user speaks naturally. Do not require the user to memorize or manually run scripts.
- Translate normal requests into the unified entrypoint and execute the command yourself.
- Keep advanced commands as a diagnostic fallback, not the normal interaction.

## Routing

- `开始工作`: run `otw.py start --repo-root <project>`.
- `继续`: run `otw.py continue --repo-root <project>`.
- `收工`: run `otw.py close --repo-root <project> --verification <evidence>`, execute or reject every receipt candidate, then resolve all candidates before reporting completion.
- Attach current project: run `otw.py attach --repo-root <project>`.
- Install and initialize once: run `otw.py setup`; provide a private root only when automatic sibling discovery is not desired.
- Update ObsidianToWiki: run `otw.py update`. Use `otw.py update --check` for a report-only check.
- Retrieve wiki context: run `otw.py search <query> --repo-root <project> --format context`.
- Ingest a source: run `otw.py ingest <source> --scope personal|project --repo-root <project>`.
- Use `otw.py upgrade --apply` only for an explicit local compatibility repair; normal product updates go through `otw.py update`.

## Boundaries

- Read `wiki.context.json` when present; it owns real local paths and is intentionally ignored by Git.
- Never infer or hard-code a private wiki path into committed project files.
- Honor `wiki.private.json`. Never open, index, ingest, summarize, or send excluded paths to a model through ObsidianToWiki.
- A private policy protects ObsidianToWiki access paths; it is not an operating-system sandbox for unrelated tools.
- Markdown remains the source of truth. Retrieval indexes are disposable caches.
- Safe upgrades may update only unmodified managed assets. Preserve modified project/private files and review `.new` candidates.
- Project `AGENTS.md` and `CLAUDE.md` are peer entrypoints. Do not make one the parent of the other.
