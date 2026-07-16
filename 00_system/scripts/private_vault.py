from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from sync_private_vault import CANDIDATE_REL_ROOT, sync_private_vault
from wiki_lib import persist_user_wiki_root


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent.parent
SEED_FILES = ("Home.md", "index.md", "log.md")
SEED_DIRECTORIES = (
    "00_system/registry",
    "01_inbox/raw",
    "01_inbox/source-notes",
    "10_personal",
    "20_projects/active",
    "20_projects/incubating",
    "20_projects/archived",
    "30_shared",
    "40_outputs",
    "90_archive",
)
LEGACY_PUBLIC_ENTRY_HASHES = {
    "AGENTS.md": "a1058b602d9af9378fb314dfb20f572913b31e6f2a1143fd2dad6cdbf9bb9b4c",
    "CLAUDE.md": "ccec114dff185480697ca87b2abb3b51603959d43f77ed19fccb1bab89b901aa",
}


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


def rendered_private_entry(source_root: Path, private_root: Path, file_name: str) -> bytes:
    template = source_root / "docs" / "templates" / f"private-{file_name}"
    text = template.read_text(encoding="utf-8")
    text = text.replace("{{PRIVATE_VAULT_ROOT}}", private_root.as_posix())
    text = text.replace("{{PUBLIC_RUNTIME_ROOT}}", source_root.as_posix())
    return text.encode("utf-8")


def normalized_text_hash(content: bytes) -> str:
    text = content.decode("utf-8").replace("\r\n", "\n").rstrip() + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def install_private_entry(source_root: Path, private_root: Path, file_name: str) -> dict[str, str]:
    destination = private_root / file_name
    desired = rendered_private_entry(source_root, private_root, file_name)
    if not destination.exists():
        write_atomic(destination, desired)
        return {"path": file_name, "action": "created"}
    if destination.read_bytes() == desired:
        return {"path": file_name, "action": "current"}

    legacy_source = source_root / file_name
    destination_bytes = destination.read_bytes()
    if (legacy_source.exists() and destination_bytes == legacy_source.read_bytes()) or normalized_text_hash(
        destination_bytes
    ) == LEGACY_PUBLIC_ENTRY_HASHES.get(file_name):
        write_atomic(destination, desired)
        return {"path": file_name, "action": "legacy_migrated"}

    candidate = private_root / CANDIDATE_REL_ROOT / f"{file_name}.new"
    write_atomic(candidate, desired)
    return {"path": file_name, "action": "conflict_staged", "candidate": str(candidate)}


def initialize_private_vault(source_root: Path, private_root: Path) -> dict[str, object]:
    source_root = source_root.expanduser().resolve()
    private_root = private_root.expanduser().resolve()
    if not source_root.exists():
        raise ValueError(f"public runtime does not exist: {source_root}")
    private_root.mkdir(parents=True, exist_ok=True)
    actions: list[dict[str, str]] = []
    for relative in SEED_DIRECTORIES:
        destination = private_root / relative
        if not destination.exists():
            destination.mkdir(parents=True)
            actions.append({"path": relative, "action": "directory_created"})

    for file_name in SEED_FILES:
        destination = private_root / file_name
        source = source_root / file_name
        if not destination.exists() and source.exists():
            write_atomic(destination, source.read_bytes())
            actions.append({"path": file_name, "action": "seeded"})

    policy = private_root / "wiki.private.json"
    if not policy.exists():
        example = source_root / "docs" / "templates" / "wiki.private.example.json"
        content = example.read_bytes() if example.exists() else b'{"schema_version": 1, "ai_access": {"excluded_paths": [], "excluded_globs": []}}\n'
        write_atomic(policy, content)
        actions.append({"path": "wiki.private.json", "action": "seeded"})

    for file_name in ("AGENTS.md", "CLAUDE.md"):
        actions.append(install_private_entry(source_root, private_root, file_name))

    sync_report = sync_private_vault(source_root, private_root, initialize=True)
    config_path = persist_user_wiki_root(private_root)
    return {
        "schema_version": 1,
        "source_root": str(source_root),
        "private_root": str(private_root),
        "user_config": str(config_path),
        "seed_actions": actions,
        "sync": sync_report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize or safely refresh an ObsidianToWiki private vault.")
    parser.add_argument("--source-root", default=str(SOURCE_ROOT))
    parser.add_argument("--private-root", required=True)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    try:
        payload = initialize_private_vault(Path(args.source_root), Path(args.private_root))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"private_root={payload['private_root']}")
    for action in payload["seed_actions"]:
        print(f"{action['action']}: {action['path']}")
    summary = payload["sync"]["summary"]
    print(f"created={summary['created']} updated={summary['updated']} conflicts={summary['conflict_staged']}")


if __name__ == "__main__":
    main()
