---
name: obsidiantowiki-retrieval
description: Retrieve durable project, personal, and shared knowledge from ObsidianToWiki before answering questions that depend on prior decisions, architecture, sources, or cross-session memory.
---

# ObsidianToWiki Retrieval

Use this skill when the task depends on facts that may already exist in the attached wiki.

1. Read `wiki.context.json` and the relevant local project control files first.
2. Derive a concise retrieval query from the user's task.
3. Run `python scripts/ai/wiki-search.py "<query>" --format context --token-budget 2000 --limit 5`.
4. Add `--project <project-slug>`, `--type <page-type>`, or `--tag <tag>` when the task has a clear scope.
5. Ground the answer in returned paths, headings, snippets, and `source_refs`. Do not invent missing provenance.
6. Query again with narrower terms only when the first context pack is insufficient.

The wrapper calls the private wiki retrieval runtime. Do not duplicate search logic in this skill and do not edit the derived SQLite index.
