from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent.parent
TEMPLATE_PATH = SOURCE_ROOT / "docs" / "templates" / "global-skills" / "obsidiantowiki-manager" / "SKILL.md"
STATE_NAME = ".obsidiantowiki-install.json"


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    finally:
        temporary = Path(temp_name)
        if temporary.exists():
            temporary.unlink()


def rendered_skill(source_root: Path) -> bytes:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return template.replace("{{source_root}}", source_root.resolve().as_posix()).encode("utf-8")


def install_one(target_root: Path, source_root: Path) -> dict[str, str]:
    skill_dir = target_root.expanduser().resolve() / "obsidiantowiki-manager"
    target = skill_dir / "SKILL.md"
    state_path = skill_dir / STATE_NAME
    desired = rendered_skill(source_root)
    desired_hash = digest_bytes(desired)
    previous_hash = ""
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(state, dict):
                previous_hash = str(state.get("managed_hash") or "")
        except json.JSONDecodeError:
            previous_hash = ""

    current_hash = digest_bytes(target.read_bytes()) if target.exists() else ""
    if current_hash == desired_hash:
        action = "current"
    elif not target.exists() or (previous_hash and current_hash == previous_hash):
        write_atomic(target, desired)
        write_atomic(
            state_path,
            (json.dumps({"schema_version": 1, "managed_hash": desired_hash}, indent=2) + "\n").encode("utf-8"),
        )
        action = "installed" if not current_hash else "updated"
    else:
        candidate = skill_dir / "SKILL.md.new"
        write_atomic(candidate, desired)
        action = "conflict_staged"
    return {"target": str(target), "action": action}


def main() -> None:
    parser = argparse.ArgumentParser(description="Install or safely upgrade the global ObsidianToWiki manager Skill.")
    parser.add_argument("--provider", choices=["agents", "claude", "all"], default="all")
    parser.add_argument("--source-root", default=str(SOURCE_ROOT))
    parser.add_argument("--agents-root", default=str(Path.home() / ".agents" / "skills"))
    parser.add_argument("--claude-root", default=str(Path.home() / ".claude" / "skills"))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    targets: list[Path] = []
    if args.provider in {"agents", "all"}:
        targets.append(Path(args.agents_root))
    if args.provider in {"claude", "all"}:
        targets.append(Path(args.claude_root))
    results = [install_one(target, Path(args.source_root)) for target in targets]
    if args.format == "json":
        print(json.dumps({"schema_version": 1, "results": results}, ensure_ascii=False, indent=2))
    else:
        for result in results:
            print(f"{result['action']}: {result['target']}")


if __name__ == "__main__":
    main()
