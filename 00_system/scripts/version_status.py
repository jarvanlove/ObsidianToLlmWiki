from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from wiki_lib import VAULT_ROOT, write_text


def repo_status(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--short"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        return [f"! git status failed for {repo_root}"]
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return lines or ["clean"]


def render_report(public_root: Path, private_root: Path) -> str:
    public_status = repo_status(public_root)
    private_status = repo_status(private_root)
    lines = [
        "# Version Status",
        "",
        f"- public_root: `{public_root}`",
        f"- private_root: `{private_root}`",
        "",
        "## Public Repo",
        "",
    ]
    lines.extend(f"- {line}" for line in public_status)
    lines.extend(["", "## Private Repo", ""])
    lines.extend(f"- {line}" for line in private_status)
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成公开仓库与私有 vault 的版本状态报告。")
    parser.add_argument("--private-root", default=str(VAULT_ROOT.parent / f"{VAULT_ROOT.name}-private"), help="私有 vault 根目录")
    parser.add_argument("--output", default=str(VAULT_ROOT / "docs" / "plans" / "version-status.md"), help="输出报告路径")
    args = parser.parse_args()

    private_root = Path(args.private_root).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    content = render_report(VAULT_ROOT, private_root)
    write_text(output_path, content)
    print(output_path)


if __name__ == "__main__":
    main()
