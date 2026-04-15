# Contributing

## Scope

This repository is a scaffold for an LLM-maintained Obsidian wiki. Contributions should improve the system itself:

- structure
- templates
- scripts
- documentation
- cross-platform behavior

Do not contribute personal knowledge, private sources, or generated local usage data.

## Before Opening a PR

1. Keep repository content generic and reusable.
2. Avoid committing local vault state, cache files, or machine-specific paths.
3. Prefer updating templates and docs over adding one-off examples.
4. Ensure new docs use Obsidian wikilinks where internal references matter.
5. If you change scripts, keep behavior consistent across Windows and macOS/Linux wrappers.

## Content Rules

- Do not commit proprietary raw source files unless they are explicitly intended as redistributable examples.
- Do not commit personal logs or private notes.
- Do not hardcode local absolute paths in docs or scripts.
- Keep example project names generic.

## Validation Checklist

- Rebuild indexes
- Run wiki lint
- Check README and manual for path portability
- Verify new pages are linked into the vault graph

## Pull Request Guidance

- Explain the problem being solved.
- Keep changes scoped.
- Mention any assumptions or tradeoffs.
- Call out follow-up work if the change only completes part of the workflow.
