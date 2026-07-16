import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import CallToolResult, TextContent
except ImportError as exc:
    raise SystemExit(
        "The optional MCP SDK is required. Install 00_system/requirements-mcp.txt first."
    ) from exc

from wiki_lib import detect_wiki_root


SCRIPT_DIR = Path(__file__).resolve().parent
SEARCH_SCRIPT = SCRIPT_DIR / "search_wiki.py"
mcp = FastMCP("ObsidianToWiki Retrieval", json_response=True)


def run_search(
    query: str,
    *,
    output_format: str,
    limit: int,
    project: str,
    page_type: str,
    tag: str,
    token_budget: int = 2000,
) -> str:
    wiki_root = detect_wiki_root(repo_root=Path.cwd())
    command = [
        sys.executable,
        str(SEARCH_SCRIPT),
        query,
        "--format",
        output_format,
        "--limit",
        str(max(1, min(limit, 20))),
        "--no-log-failures",
    ]
    if project.strip():
        command.extend(["--project", project.strip()])
    if page_type.strip():
        command.extend(["--type", page_type.strip()])
    if tag.strip():
        command.extend(["--tag", tag.strip()])
    if output_format == "context":
        command.extend(["--token-budget", str(max(100, min(token_budget, 8000)))])

    env = os.environ.copy()
    env["OBSIDIAN_WIKI_ROOT"] = str(wiki_root)
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "wiki search failed")
    return completed.stdout


@mcp.tool()
def search_wiki(
    query: str,
    limit: int = 5,
    project: str = "",
    page_type: str = "",
    tag: str = "",
) -> CallToolResult:
    """Search durable wiki knowledge and return structured, source-located results."""
    payload = json.loads(
        run_search(
            query,
            output_format="json",
            limit=limit,
            project=project,
            page_type=page_type,
            tag=tag,
        )
    )
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))],
        structuredContent=payload,
    )


@mcp.tool(structured_output=False)
def get_wiki_context(
    query: str,
    token_budget: int = 2000,
    limit: int = 5,
    project: str = "",
    page_type: str = "",
    tag: str = "",
) -> CallToolResult:
    """Return a bounded context pack with paths, headings, snippets, and source references."""
    context_pack = run_search(
        query,
        output_format="context",
        limit=limit,
        project=project,
        page_type=page_type,
        tag=tag,
        token_budget=token_budget,
    )
    return CallToolResult(content=[TextContent(type="text", text=context_pack)])


if __name__ == "__main__":
    mcp.run(transport="stdio")
