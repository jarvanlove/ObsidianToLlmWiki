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

- `开始工作`: run `otw.py start --repo-root <project> [--task <request>]`; use its bounded Context Receipt without asking the user to maintain the wiki.
- `继续`: run `otw.py continue --repo-root <project> [--task <request>]`; keep the active task identity and rerun the read-only Context/budget check.
- `收工`: run `otw.py close --repo-root <project> --verification <evidence> [--ui-task <id>]`, execute or reject every receipt candidate, then resolve all candidates. Resolution automatically compiles eligible memory and refreshes bounded projections and the cockpit.
- Attach current project: run `otw.py attach --repo-root <project>`.
- Install and initialize once: run `otw.py setup`; provide a private root only when automatic sibling discovery is not desired.
- Update ObsidianToWiki: run `otw.py update`. Use `otw.py update --check` for a report-only check.
- Retrieve wiki context: run `otw.py search <query> --repo-root <project> --format context`.
- Ingest a source: run `otw.py ingest <source> --scope personal|project --repo-root <project>`.
- Use `otw.py upgrade --apply` only for an explicit local compatibility repair; normal product updates go through `otw.py update`.

## UI Governance

For a task that changes a user-facing screen, interaction, layout, visual system, or responsive behavior, classify UI impact before writing production UI:

- `U0`: no UI impact. Use the normal lifecycle.
- `U1`: local change within an approved design system. Reuse the project UI contract and collect visual evidence.
- `U2`: new or materially redesigned user flow. Produce a direction candidate and obtain explicit Design Authority approval before implementation.
- `U3`: design-system or global visual change. Require an approved direction and Design RFC before implementation.

Keep this classification, tokens, task files, and approvals internal. Do not ask a normal user to choose a palette, learn a level, run a command, or understand an RFC.

### Simple visual experience

- When the user gives no visual preference, silently reuse the project baseline. If the project has none, use the fixed fallback; never ask the user to choose from the palette library first and never randomize.
- When a user says the result feels too cold, plain, busy, unprofessional, or otherwise unsatisfactory, first decide whether the complaint is local (spacing, hierarchy, copy, component state) or visual-directional. Fix local issues without proposing a palette change.
- For a visual-directional complaint, run `otw.py ui recommend-directions --feedback <user-feedback> --product-context <task-context>`. Present exactly three returned recommendations as numbered plain-language choices: label and one-sentence outcome only. Do not show hex values, tiers, token names, or all 19 sources.
- Accept `1`, `2`, `3`, `第一个`, `第二个`, `第三个`, `就这个`, or an equivalent natural confirmation. Before direction approval, record it with `otw.py ui select-direction --task-id <id> --visual-direction <id> --approval-note <user-confirmation>`.
- If the project already has a baseline and the user wants a different overall feel, explain it as an overall style adjustment, not a technical gate. Run it as U3 so the project cannot drift into page-by-page visual inconsistency.
- Offer controlled directions only when the user asks to see more options or names one; reference-only directions remain invisible inspiration, not selectable production themes.

For U1+ use `otw.py ui assess`, then `otw.py ui init` with a stable task id. Read `docs/design/UI_CONTRACT.md`, `docs/design/UI_VISUAL_BASELINE.json` when present, and the generated task file before using a UI Skill. Record a user-named Skill as `--requested-skill`; it is an executor, never design authority. Generic "make it prettier" Skills are candidate-only unless the project registry grants a narrower role.

When the task lacks an approved visual reference, use the runtime visual-direction registry. Its fallback is fixed, not random. A controlled direction must be explicitly selected by the user and recorded on the UI task; a reference-only palette cannot become a production baseline. Keep the existing project baseline for U1/U2 work. A U3 task may change it only after its Design RFC is approved.

Use Stitch only for visual exploration or prototype candidates. Use Figma nodes as authority only when the task records them as approved. Do not copy generated design-tool code directly into production without the project component/token constraints.

Before U2/U3 implementation, record `direction_approved` with the user's approval note. For U3, record the approved RFC with `otw.py ui approve-rfc`. Before closing any U1+ task, record screenshot, Visual QA, and accessibility evidence, run `otw.py ui check --phase close`, then pass `--ui-task <id>` to `otw.py close`.

## Boundaries

- Read `wiki.context.json` when present; it owns real local paths and is intentionally ignored by Git.
- Never infer or hard-code a private wiki path into committed project files.
- Never compile a pending receipt. If automatic maintenance fails, keep the verified task result, surface `pending_memory_repair`, and do not claim a P1/P0 governance close until required history is repaired.
- Honor `wiki.private.json`. Never open, index, ingest, summarize, or send excluded paths to a model through ObsidianToWiki.
- A private policy protects ObsidianToWiki access paths; it is not an operating-system sandbox for unrelated tools.
- Markdown remains the source of truth. Retrieval indexes are disposable caches.
- Safe upgrades may update only unmodified managed assets. Preserve modified project/private files and review `.new` candidates.
- Project `AGENTS.md` and `CLAUDE.md` are peer entrypoints. Do not make one the parent of the other.
- Do not silently alter a user's global Codex/Claude/third-party UI Skill configuration. Project registry rules control project-owned execution; report conflicts and ask for explicit approval before changing user-level configuration.
