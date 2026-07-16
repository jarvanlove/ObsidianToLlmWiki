# Agent Retrieval

The project Skill and MCP server are thin consumers of the same retrieval contract.

- Install project adapters with `attach_project.py --install-ai-adapters`.
- The project Skill decides when durable wiki context is needed.
- `scripts/ai/wiki-search.py` reads `wiki.context.json` and calls the private runtime.
- `mcp_retrieval_server.py` exposes read-only `search_wiki` and `get_wiki_context` tools over stdio.
- Configure the MCP server once per AI tool when that tool can launch it from the active project; do not create a second retrieval implementation per provider.

Install the optional official Python SDK:

```text
python -m pip install -r <private-wiki-root>/00_system/requirements-mcp.txt
```

The MCP tools never edit Markdown or the SQLite cache directly. Normal search freshness rules still apply.
