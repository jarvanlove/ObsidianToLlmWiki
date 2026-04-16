from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from wiki_lib import VAULT_ROOT, write_text


GROUP_RULES = [
    ("core", ("00_system/scripts/", "00_system/templates/", "00_system/registry/")),
    ("docs", ("README", "README-zh", "使用手册.md", "docs/", "30_shared/prompts/")),
    ("generated", ("index.md", "10_personal/索引.md", "20_projects/索引.md", "20_projects/关系索引.md", "30_shared/索引.md", "40_outputs/索引.md", "40_outputs/analyses/")),
    ("other", ()),
]


def repo_status(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--short"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line.strip()] if result.returncode == 0 else []


def classify_path(path: str) -> str:
    for name, prefixes in GROUP_RULES:
        if any(path.startswith(prefix) or path == prefix for prefix in prefixes):
            return name
    return "other"


def parse_status_line(line: str) -> tuple[str, str]:
    status = line[:3].strip()
    path = line[3:].strip().strip('"')
    return status, path


def render_grouped(repo_name: str, lines: list[str]) -> list[str]:
    grouped: dict[str, list[str]] = {name: [] for name, _ in GROUP_RULES}
    grouped["other"] = []
    for line in lines:
        status, path = parse_status_line(line)
        group = classify_path(path)
        grouped.setdefault(group, []).append(f"- `{status}` {path}")

    output = [f"## {repo_name}", ""]
    for group_name, _ in GROUP_RULES:
        items = grouped.get(group_name, [])
        if not items:
            continue
        output.append(f"### {group_name}")
        output.append("")
        output.extend(items)
        output.append("")
    if not any(grouped.values()):
        output.append("- clean")
        output.append("")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="生成按提交分组整理的版本收口报告。")
    parser.add_argument("--private-root", default=str(VAULT_ROOT.parent / f"{VAULT_ROOT.name}-private"), help="私有 vault 根目录")
    parser.add_argument("--output", default=str(VAULT_ROOT / "docs" / "plans" / "version-closure-report.md"), help="输出报告路径")
    args = parser.parse_args()

    private_root = Path(args.private_root).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    public_lines = repo_status(VAULT_ROOT)
    private_lines = repo_status(private_root)

    report = [
        "# Version Closure Report",
        "",
        "按提交分组整理当前公开仓库与私有 vault 的变更，方便进入提交阶段。",
        "",
        *render_grouped("Public Repo", public_lines),
        *render_grouped("Private Repo", private_lines),
    ]
    write_text(output_path, "\n".join(report))
    print(output_path)


if __name__ == "__main__":
    main()
