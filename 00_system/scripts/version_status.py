from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from wiki_lib import detect_wiki_root, write_text


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent.parent


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def git_status(repo_root: Path) -> dict[str, object]:
    result = subprocess.run(
        ["git", "status", "--short"], cwd=repo_root, capture_output=True, text=True, encoding="utf-8", check=False
    )
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, capture_output=True, text=True, encoding="utf-8", check=False
    )
    return {
        "available": result.returncode == 0,
        "commit": commit.stdout.strip() if commit.returncode == 0 else "",
        "changes": [line for line in result.stdout.splitlines() if line.strip()] if result.returncode == 0 else [],
    }


def build_status(public_root: Path, private_root: Path) -> dict[str, object]:
    release = load_json(public_root / "00_system/registry/runtime_release.json")
    vault = load_json(private_root / "00_system/registry/vault_state.json")
    private = load_json(private_root / "00_system/registry/private_scaffold_state.json")
    projects_path = private_root / "00_system/registry/projects.json"
    try:
        projects_payload = json.loads(projects_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        projects_payload = []
    projects = projects_payload if isinstance(projects_payload, list) else []
    project_status: list[dict[str, object]] = []
    for item in projects:
        if not isinstance(item, dict):
            continue
        repo_root = Path(str(item.get("project_repo_root") or "")).expanduser()
        context = load_json(repo_root / "wiki.context.json") if repo_root.exists() else {}
        project_status.append(
            {
                "project_slug": str(item.get("project_slug") or ""),
                "repo_root": str(repo_root),
                "exists": repo_root.exists(),
                "project_scaffold_version": context.get("project_scaffold_version", 0),
                "runtime_root": str(context.get("runtime_root") or ""),
            }
        )
    candidates = private_root / "40_outputs/upgrade-candidates/private-scaffold"
    return {
        "schema_version": 1,
        "public_root": str(public_root),
        "private_root": str(private_root),
        "runtime_release": release,
        "public_git": git_status(public_root),
        "vault_schema_version": vault.get("vault_schema_version", 0),
        "private_scaffold_version": private.get("private_scaffold_version", 0),
        "private_conflict_candidates": len(list(candidates.rglob("*.new"))) if candidates.exists() else 0,
        "projects": project_status,
    }


def render_markdown(payload: dict[str, object]) -> str:
    release = payload["runtime_release"] if isinstance(payload["runtime_release"], dict) else {}
    git = payload["public_git"] if isinstance(payload["public_git"], dict) else {}
    lines = [
        "# Version Status",
        "",
        f"- runtime_version: `{release.get('runtime_version', 'unknown')}`",
        f"- public_commit: `{git.get('commit', '')}`",
        f"- public_dirty_files: `{len(git.get('changes', []))}`",
        f"- vault_schema_version: `{payload['vault_schema_version']}`",
        f"- private_scaffold_version: `{payload['private_scaffold_version']}`",
        f"- private_conflict_candidates: `{payload['private_conflict_candidates']}`",
        "",
        "## Attached Projects",
        "",
    ]
    projects = payload.get("projects") if isinstance(payload.get("projects"), list) else []
    if not projects:
        lines.append("- None registered.")
    for item in projects:
        lines.append(
            f"- `{item['project_slug']}`: exists={item['exists']} project_scaffold={item['project_scaffold_version']}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Report public runtime, private scaffold, vault, and project bridge versions.")
    parser.add_argument("--public-root", default=str(SOURCE_ROOT))
    parser.add_argument("--private-root", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()
    public_root = Path(args.public_root).expanduser().resolve()
    private_root = (
        Path(args.private_root).expanduser().resolve()
        if args.private_root
        else detect_wiki_root(repo_root=public_root)
    )
    payload = build_status(public_root, private_root)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_markdown(payload)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        write_text(output, content)
        print(output)
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
