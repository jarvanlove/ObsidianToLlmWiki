# Retrieval Adapters

The retrieval Skill is installed per project because its activation belongs to that project's AI control layer. The MCP server itself can be configured once per AI tool because it discovers the current project's `wiki.context.json` or the user's saved wiki root.

## Project Skill

- Codex and Agent Skills compatible tools: `.agents/skills/obsidiantowiki-retrieval/SKILL.md`
- Claude Code: `.claude/skills/obsidiantowiki-retrieval/SKILL.md`
- Provider-neutral command: `python scripts/ai/wiki-search.py "query" --format context`

The Skill decides when retrieval is useful. It does not own ranking, indexing, or wiki paths.

## MCP Runtime

Install the optional official Python SDK once:

```text
python -m pip install -r <private-wiki-root>/00_system/requirements-mcp.txt
```

The project-local launcher is:

```text
python scripts/ai/wiki-mcp.py
```

It exposes two read-only tools:

- `search_wiki`: stable structured JSON results
- `get_wiki_context`: bounded context pack for direct model consumption

Do not configure a separate MCP server per project unless the AI tool requires project-scoped configuration. The launcher and server discover the active project bridge at runtime.
