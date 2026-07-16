from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from install_manager_skill import install_one
from private_vault import initialize_private_vault
from project_adapter import apply_adapter_upgrade, inspect_adapter
from project_scaffold import upgrade_registered_projects
from sync_private_vault import record_matching_baseline, iter_source_files, load_manifest, selected_managed_roots


SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_ROOT = SCRIPT_DIR.parent.parent


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(detail or f"command failed: {' '.join(command)}")
    return completed.stdout.strip()


def managed_python(source_root: Path) -> Path:
    candidate = source_root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return candidate if candidate.exists() else Path(sys.executable)


def runtime_version(source_root: Path) -> str:
    path = source_root / "00_system" / "registry" / "runtime_release.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "unknown"
    return str(payload.get("runtime_version") or "unknown") if isinstance(payload, dict) else "unknown"


def install_skills(source_root: Path, provider: str) -> list[dict[str, str]]:
    targets: list[Path] = []
    if provider in {"agents", "all"}:
        targets.append(Path.home() / ".agents" / "skills")
    if provider in {"claude", "all"}:
        targets.append(Path.home() / ".claude" / "skills")
    return [install_one(target, source_root) for target in targets]


def run_vault_maintenance(source_root: Path, private_root: Path) -> dict[str, str]:
    python = managed_python(source_root)
    env = os.environ.copy()
    env["OBSIDIAN_WIKI_ROOT"] = str(private_root)
    env["PYTHONIOENCODING"] = "utf-8"
    outputs: dict[str, str] = {}
    outputs["vault_migration"] = run(
        [str(python), str(source_root / "00_system/scripts/vault_compat.py"), "migrate", "--apply"],
        cwd=source_root,
        env=env,
    )
    outputs["shared_assets"] = run(
        [
            str(python),
            str(source_root / "00_system/scripts/shared_assets.py"),
            "apply-safe",
            "--vault-root",
            str(private_root),
            "--source-root",
            str(source_root),
        ],
        cwd=source_root,
        env=env,
    )
    outputs["indexes"] = run(
        [str(python), str(source_root / "00_system/scripts/rebuild_indexes.py")], cwd=source_root, env=env
    )
    outputs["doctor"] = run(
        [
            str(python),
            str(source_root / "00_system/scripts/doctor.py"),
            "--repo-root",
            str(private_root),
            "--wiki-root",
            str(private_root),
            "--strict",
        ],
        cwd=source_root,
        env=env,
    )
    return outputs


def upgrade_projects(source_root: Path, private_root: Path) -> list[dict[str, object]]:
    reports = upgrade_registered_projects(private_root, source_root)
    for report in reports:
        if report.get("status") != "updated":
            continue
        repo_root = Path(str(report["repo_root"]))
        adapter = inspect_adapter(repo_root)
        if adapter.get("status") != "not_installed":
            report["optional_adapter"] = apply_adapter_upgrade(repo_root)
    return reports


def write_receipt(private_root: Path, payload: dict[str, object]) -> Path:
    receipt_path = private_root / "00_system" / "registry" / "runtime_update_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt_path


def setup_runtime(source_root: Path, private_root: Path, provider: str) -> dict[str, object]:
    source_root = source_root.expanduser().resolve()
    private_root = private_root.expanduser().resolve()
    initialized = initialize_private_vault(source_root, private_root)
    projects = upgrade_projects(source_root, private_root)
    skills = install_skills(source_root, provider)
    maintenance = run_vault_maintenance(source_root, private_root)
    payload: dict[str, object] = {
        "schema_version": 1,
        "operation": "setup",
        "status": "complete",
        "runtime_version": runtime_version(source_root),
        "completed_at": datetime.now().replace(microsecond=0).isoformat(),
        "source_root": str(source_root),
        "private_root": str(private_root),
        "private_vault": initialized,
        "skills": skills,
        "projects": projects,
        "maintenance": maintenance,
    }
    payload["receipt"] = str(write_receipt(private_root, payload))
    return payload


def git_output(source_root: Path, *args: str) -> str:
    return run(["git", *args], cwd=source_root)


def inspect_git_update(source_root: Path, *, fetch: bool) -> dict[str, object]:
    dirty = git_output(source_root, "status", "--porcelain").splitlines()
    branch = git_output(source_root, "branch", "--show-current")
    remote_url = git_output(source_root, "remote", "get-url", "origin")
    if fetch:
        git_output(source_root, "fetch", "--quiet", "origin")
    upstream = git_output(source_root, "rev-parse", "--abbrev-ref", "@{u}")
    local_commit = git_output(source_root, "rev-parse", "HEAD")
    remote_commit = git_output(source_root, "rev-parse", upstream)
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", local_commit, remote_commit], cwd=source_root, check=False
    ).returncode == 0
    return {
        "branch": branch,
        "origin": remote_url,
        "upstream": upstream,
        "local_commit": local_commit,
        "remote_commit": remote_commit,
        "dirty": dirty,
        "update_available": local_commit != remote_commit,
        "fast_forward": ancestor,
    }


def record_pre_update_baseline(source_root: Path, private_root: Path) -> int:
    manifest = load_manifest(source_root)
    roots, _categories, protected = selected_managed_roots(manifest, None, None)
    ignore = [str(value) for value in manifest.get("ignore_globs", []) if str(value).strip()]
    files = iter_source_files(source_root, roots, ignore, protected)
    actions = record_matching_baseline(source_root, private_root, files, dry_run=False)
    return len(actions)


def apply_update(source_root: Path, private_root: Path, provider: str) -> dict[str, object]:
    source_root = source_root.expanduser().resolve()
    private_root = private_root.expanduser().resolve()
    status = inspect_git_update(source_root, fetch=True)
    if status["dirty"]:
        raise RuntimeError("public runtime has uncommitted changes; commit or discard them before updating")
    if status["update_available"] and not status["fast_forward"]:
        raise RuntimeError("public runtime has diverged from its upstream; automatic update requires a fast-forward")
    baseline_count = record_pre_update_baseline(source_root, private_root) if private_root.exists() else 0
    old_commit = str(status["local_commit"])
    if status["update_available"]:
        git_output(source_root, "pull", "--ff-only")
    new_commit = git_output(source_root, "rev-parse", "HEAD")
    python = managed_python(source_root)
    run([str(python), "-m", "pip", "install", "-r", str(source_root / "00_system/requirements.txt")], cwd=source_root)
    completed = run(
        [
            str(python),
            str(source_root / "00_system/scripts/runtime_manager.py"),
            "post-update",
            "--source-root",
            str(source_root),
            "--private-root",
            str(private_root),
            "--provider",
            provider,
            "--old-commit",
            old_commit,
            "--new-commit",
            new_commit,
            "--baseline-count",
            str(baseline_count),
            "--format",
            "json",
        ],
        cwd=source_root,
    )
    return json.loads(completed)


def post_update(
    source_root: Path,
    private_root: Path,
    provider: str,
    old_commit: str,
    new_commit: str,
    baseline_count: int,
) -> dict[str, object]:
    payload = setup_runtime(source_root, private_root, provider)
    payload.update(
        {
            "operation": "update",
            "old_commit": old_commit,
            "new_commit": new_commit,
            "pre_update_baselines": baseline_count,
        }
    )
    payload["receipt"] = str(write_receipt(private_root, payload))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Install, inspect, or safely update ObsidianToWiki.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("setup", "update", "post-update"):
        command = subparsers.add_parser(name)
        command.add_argument("--source-root", default=str(SOURCE_ROOT))
        command.add_argument("--private-root", default="")
        command.add_argument("--provider", choices=["agents", "claude", "all"], default="all")
        command.add_argument("--format", choices=["text", "json"], default="text")
        if name == "update":
            command.add_argument("--check", action="store_true")
        if name == "post-update":
            command.add_argument("--old-commit", required=True)
            command.add_argument("--new-commit", required=True)
            command.add_argument("--baseline-count", type=int, default=0)
    args = parser.parse_args()
    source_root = Path(args.source_root).expanduser().resolve()
    private_root = (
        Path(args.private_root).expanduser().resolve()
        if args.private_root
        else source_root.parent / f"{source_root.name}-private"
    )
    try:
        if args.command == "setup":
            payload = setup_runtime(source_root, private_root, args.provider)
        elif args.command == "update" and args.check:
            payload = {
                "schema_version": 1,
                "operation": "update-check",
                "runtime_version": runtime_version(source_root),
                "git": inspect_git_update(source_root, fetch=True),
            }
        elif args.command == "update":
            payload = apply_update(source_root, private_root, args.provider)
        else:
            payload = post_update(
                source_root,
                private_root,
                args.provider,
                args.old_commit,
                args.new_commit,
                args.baseline_count,
            )
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"operation={payload['operation']} status={payload.get('status', 'ok')}")
        print(f"runtime_version={payload.get('runtime_version', 'unknown')}")
        if payload.get("receipt"):
            print(f"receipt={payload['receipt']}")


if __name__ == "__main__":
    main()
