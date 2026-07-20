from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from wiki_lib import slugify


UI_LEVELS = ("U0", "U1", "U2", "U3")
TASK_STAGES = ("intake", "direction", "direction_approved", "implementation", "verification", "closed")
UI_ROOT = Path("docs/design")
CONTRACT_PATH = UI_ROOT / "UI_CONTRACT.md"
REGISTRY_PATH = UI_ROOT / "UI_SKILL_REGISTRY.yaml"
TASKS_PATH = UI_ROOT / "ui-tasks"
QA_PATH = UI_ROOT / "qa"
BASELINE_PATH = UI_ROOT / "UI_VISUAL_BASELINE.json"
TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "templates" / "project-ui"
VISUAL_DIRECTION_REGISTRY = Path(__file__).resolve().parents[1] / "registry" / "ui_visual_directions.json"


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary_name, path)
    finally:
        temporary = Path(temporary_name)
        if temporary.exists():
            temporary.unlink()


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read UI task: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"UI task must be a YAML object: {path}")
    return payload


def load_visual_direction_registry() -> dict[str, Any]:
    try:
        payload = json.loads(VISUAL_DIRECTION_REGISTRY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read visual direction registry: {exc}") from exc
    directions = payload.get("directions")
    if payload.get("schema_version") != 1 or not isinstance(directions, list):
        raise ValueError("visual direction registry has an unsupported schema")
    ids = {str(item.get("id") or "") for item in directions if isinstance(item, dict)}
    if not payload.get("fallback_direction_id") in ids:
        raise ValueError("visual direction registry fallback is missing")
    return payload


def resolve_visual_direction(direction_id: str = "") -> dict[str, Any]:
    registry = load_visual_direction_registry()
    selected_id = direction_id.strip() or str(registry["fallback_direction_id"])
    for direction in registry["directions"]:
        if isinstance(direction, dict) and direction.get("id") == selected_id:
            if direction.get("tier") == "reference_only":
                raise ValueError(
                    f"visual direction {selected_id} is reference-only and cannot become a production baseline"
                )
            return direction
    raise ValueError(f"unknown visual direction: {selected_id}")


def read_visual_baseline(repo_root: Path) -> dict[str, Any] | None:
    target = repo_root / BASELINE_PATH
    if not target.is_file():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read project visual baseline: {exc}") from exc
    if payload.get("schema_version") != 1 or not isinstance(payload.get("direction"), dict):
        raise ValueError(f"unsupported project visual baseline: {BASELINE_PATH.as_posix()}")
    return payload


def write_visual_baseline(repo_root: Path, direction: dict[str, Any]) -> str:
    registry = load_visual_direction_registry()
    payload = {
        "schema_version": 1,
        "updated_at": now_iso(),
        "registry_schema_version": registry["schema_version"],
        "direction": direction,
        "shared_tokens": registry.get("shared_tokens", {}),
    }
    target = repo_root / BASELINE_PATH
    write_atomic(target, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return target.relative_to(repo_root).as_posix()


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    write_atomic(path, yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))


def task_path(repo_root: Path, task_id: str) -> Path:
    normalized = slugify(task_id)
    if normalized != task_id.strip():
        raise ValueError(f"UI task id must be a stable slug: {normalized}")
    return repo_root / TASKS_PATH / f"{normalized}.yaml"


def repo_relative_path(repo_root: Path, value: str) -> str:
    candidate = Path(value).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()
    try:
        relative = resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"UI evidence must stay inside the project repository: {value}") from exc
    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"UI evidence file is missing: {relative.as_posix()}")
    return relative.as_posix()


def level_requirements(level: str) -> dict[str, Any]:
    if level not in UI_LEVELS:
        raise ValueError(f"unsupported UI level: {level}")
    if level == "U0":
        return {
            "requires_ui_contract": False,
            "requires_direction_approval": False,
            "requires_visual_evidence": False,
            "description": "No user-facing UI impact. Use the normal project lifecycle.",
        }
    if level == "U1":
        return {
            "requires_ui_contract": True,
            "requires_direction_approval": False,
            "requires_visual_evidence": True,
            "description": "Local UI change within the approved design system.",
        }
    if level == "U2":
        return {
            "requires_ui_contract": True,
            "requires_direction_approval": True,
            "requires_visual_evidence": True,
            "description": "New or materially redesigned user flow. Approve direction before production implementation.",
        }
    return {
        "requires_ui_contract": True,
        "requires_direction_approval": True,
        "requires_visual_evidence": True,
        "description": "Design-system or global visual change. Requires an approved Design RFC and direction.",
    }


def render_template(name: str, replacements: dict[str, str]) -> str:
    content = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        content = content.replace("{{" + key + "}}", value)
    return content


def ensure_project_ui_files(repo_root: Path) -> list[str]:
    created: list[str] = []
    for relative, template in ((CONTRACT_PATH, "UI_CONTRACT.md"), (REGISTRY_PATH, "UI_SKILL_REGISTRY.yaml")):
        target = repo_root / relative
        if target.exists():
            continue
        write_atomic(target, render_template(template, {"TODAY": datetime.now().date().isoformat()}))
        created.append(relative.as_posix())
    for directory in (repo_root / TASKS_PATH, repo_root / QA_PATH, repo_root / UI_ROOT / "decisions", repo_root / UI_ROOT / "references"):
        directory.mkdir(parents=True, exist_ok=True)
    return created


def assess(task: str, level: str, requested_skill: str = "") -> dict[str, Any]:
    requirements = level_requirements(level)
    fallback = resolve_visual_direction()
    return {
        "schema_version": 1,
        "task": task.strip(),
        "ui_level": level,
        "requested_skill": requested_skill.strip(),
        "fallback_visual_direction": {"id": fallback["id"], "name": fallback["name"]},
        "requirements": requirements,
        "next_action": "init" if level != "U0" else "normal_lifecycle",
    }


def initialize_task(
    repo_root: Path,
    task_id: str,
    title: str,
    level: str,
    requested_skill: str = "",
    visual_direction_id: str = "",
    approval_note: str = "",
) -> dict[str, Any]:
    requirements = level_requirements(level)
    if level == "U0":
        return {
            "schema_version": 1,
            "status": "not_created",
            "reason": "U0 tasks use the normal lifecycle and do not create UI governance files.",
        }
    existing_baseline = read_visual_baseline(repo_root)
    baseline_direction = existing_baseline.get("direction") if existing_baseline else None
    requested_id = visual_direction_id.strip() or str((baseline_direction or {}).get("id") or "")
    direction = resolve_visual_direction(requested_id)
    selection = "explicit" if visual_direction_id.strip() else "project_baseline" if baseline_direction else "fallback"
    baseline_change = bool(baseline_direction and baseline_direction.get("id") != direction.get("id"))
    if baseline_change and level != "U3":
        raise ValueError("project visual baseline is locked; a different direction requires a U3 task and approved RFC")
    if level == "U1" and direction.get("tier") == "controlled" and not approval_note.strip():
        raise ValueError("a controlled visual direction requires an explicit user selection note")
    created = ensure_project_ui_files(repo_root)
    target = task_path(repo_root, task_id)
    if target.exists():
        raise ValueError(f"UI task already exists: {target.relative_to(repo_root).as_posix()}")
    initial_stage = "implementation" if level == "U1" else "direction"
    payload = {
        "schema_version": 1,
        "id": task_id,
        "title": title.strip(),
        "ui_level": level,
        "stage": initial_stage,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "scope": {"routes": [], "states": ["default", "loading", "empty", "error"], "viewports": ["1440x900", "390x844"]},
        "design_authority": {"owner": "TODO", "sources": [], "approved_direction": ""},
        "visual_direction": {
            "id": direction["id"],
            "name": direction["name"],
            "tier": direction["tier"],
            "selection": selection,
            "selection_note": approval_note.strip(),
            "baseline_change": baseline_change,
        },
        "skill_governance": {
            "requested_skill": requested_skill.strip(),
            "automatic_skills": [
                "project-ui-rules",
                "ui-visual-direction-registry",
                "ui-accessibility-check",
                "ui-screenshot-check",
            ],
            "explicit_skills": [],
        },
        "constraints": {"allow_new_dependencies": False, "baseline_update_requires_approval": True},
        "approvals": {"visual_direction": "not_required" if level == "U1" else "pending", "design_rfc": "pending" if level == "U3" else "not_required", "release": "pending"},
        "evidence": {"screenshots": [], "visual_qa_report": "", "accessibility_reports": [], "notes": []},
        "requirements": requirements,
    }
    write_yaml(target, payload)
    qa_target = repo_root / QA_PATH / f"{task_id}.md"
    created_files = created + [target.relative_to(repo_root).as_posix()]
    if not qa_target.exists():
        write_atomic(
            qa_target,
            render_template("UI_VISUAL_QA.md", {"TASK_ID": task_id, "TASK_TITLE": title.strip()}),
        )
        created_files.append(qa_target.relative_to(repo_root).as_posix())
    if level == "U3":
        rfc_target = repo_root / UI_ROOT / "decisions" / f"UI-RFC-{task_id}.md"
        if not rfc_target.exists():
            write_atomic(rfc_target, render_template("UI_DESIGN_RFC.md", {"TITLE": title.strip()}))
            created_files.append(rfc_target.relative_to(repo_root).as_posix())
    if level == "U1" and not existing_baseline:
        created_files.append(write_visual_baseline(repo_root, direction))
    return {
        "schema_version": 1,
        "status": "created",
        "task_path": target.relative_to(repo_root).as_posix(),
        "stage": initial_stage,
        "created_files": created_files,
    }


def load_task(repo_root: Path, task_id: str) -> tuple[Path, dict[str, Any]]:
    target = task_path(repo_root, task_id)
    if not target.exists():
        raise ValueError(f"UI task is missing: {target.relative_to(repo_root).as_posix()}")
    payload = read_yaml(target)
    if payload.get("schema_version") != 1:
        raise ValueError(f"unsupported UI task schema: {target.relative_to(repo_root).as_posix()}")
    level = str(payload.get("ui_level") or "")
    level_requirements(level)
    return target, payload


def set_stage(repo_root: Path, task_id: str, stage: str, approval_note: str = "") -> dict[str, Any]:
    if stage not in TASK_STAGES:
        raise ValueError(f"unsupported UI stage: {stage}")
    target, payload = load_task(repo_root, task_id)
    level = str(payload["ui_level"])
    approvals = payload.setdefault("approvals", {})
    if not isinstance(approvals, dict):
        raise ValueError("UI task approvals must be an object")
    if stage == "direction_approved":
        if level not in {"U2", "U3"}:
            raise ValueError("only U2/U3 tasks require direction approval")
        if not approval_note.strip():
            raise ValueError("direction approval requires a human approval note")
        visual_direction = payload.get("visual_direction")
        if not isinstance(visual_direction, dict) or not visual_direction.get("id"):
            raise ValueError("direction approval requires a selected visual direction")
        approvals["visual_direction"] = "approved"
        payload.setdefault("design_authority", {}).update(
            {
                "approval_note": approval_note.strip(),
                "approved_at": now_iso(),
                "approved_direction": visual_direction["id"],
            }
        )
        if level == "U2" and not read_visual_baseline(repo_root):
            write_visual_baseline(repo_root, resolve_visual_direction(str(visual_direction["id"])))
    if stage == "implementation" and level in {"U2", "U3"} and approvals.get("visual_direction") != "approved":
        raise ValueError("cannot enter implementation before visual direction is approved")
    if stage == "implementation" and level == "U3" and approvals.get("design_rfc") != "approved":
        raise ValueError("cannot enter implementation before the Design RFC is approved")
    if stage == "closed":
        report = validate_task(repo_root, task_id, phase="close")
        if not report["passed"]:
            raise ValueError("cannot close UI task: " + "; ".join(report["blocking"]))
        approvals["release"] = "approved"
    payload["stage"] = stage
    payload["updated_at"] = now_iso()
    write_yaml(target, payload)
    return {"schema_version": 1, "status": "updated", "task_path": target.relative_to(repo_root).as_posix(), "stage": stage}


def approve_rfc(repo_root: Path, task_id: str, approval_note: str) -> dict[str, Any]:
    if not approval_note.strip():
        raise ValueError("Design RFC approval requires a human approval note")
    target, payload = load_task(repo_root, task_id)
    if payload.get("ui_level") != "U3":
        raise ValueError("only U3 tasks require a Design RFC approval")
    rfc_path = repo_root / UI_ROOT / "decisions" / f"UI-RFC-{task_id}.md"
    if not rfc_path.is_file():
        raise ValueError(f"missing Design RFC: {rfc_path.relative_to(repo_root).as_posix()}")
    approvals = payload.setdefault("approvals", {})
    if not isinstance(approvals, dict):
        raise ValueError("UI task approvals must be an object")
    if approvals.get("visual_direction") != "approved":
        raise ValueError("Design RFC approval requires an approved visual direction")
    visual_direction = payload.get("visual_direction")
    if not isinstance(visual_direction, dict) or not visual_direction.get("id"):
        raise ValueError("Design RFC approval requires a selected visual direction")
    approvals["design_rfc"] = "approved"
    payload.setdefault("design_authority", {}).update({"rfc_approval_note": approval_note.strip(), "rfc_approved_at": now_iso()})
    payload["updated_at"] = now_iso()
    write_yaml(target, payload)
    write_visual_baseline(repo_root, resolve_visual_direction(str(visual_direction["id"])))
    return {"schema_version": 1, "status": "updated", "task_path": target.relative_to(repo_root).as_posix(), "approval": "design_rfc"}


def record_evidence(
    repo_root: Path,
    task_id: str,
    screenshots: list[str],
    visual_qa: str,
    accessibility_reports: list[str],
    note: str,
) -> dict[str, Any]:
    target, payload = load_task(repo_root, task_id)
    evidence = payload.setdefault("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError("UI task evidence must be an object")
    existing_screenshots = [str(item) for item in evidence.get("screenshots", []) if str(item).strip()]
    existing_accessibility = [str(item) for item in evidence.get("accessibility_reports", []) if str(item).strip()]
    evidence["screenshots"] = list(dict.fromkeys(existing_screenshots + [repo_relative_path(repo_root, item) for item in screenshots]))
    evidence["accessibility_reports"] = list(
        dict.fromkeys(existing_accessibility + [repo_relative_path(repo_root, item) for item in accessibility_reports])
    )
    if visual_qa.strip():
        evidence["visual_qa_report"] = repo_relative_path(repo_root, visual_qa)
    if note.strip():
        notes = evidence.setdefault("notes", [])
        if not isinstance(notes, list):
            raise ValueError("UI task evidence notes must be a list")
        notes.append({"at": now_iso(), "note": note.strip()})
    payload["stage"] = "verification"
    payload["updated_at"] = now_iso()
    write_yaml(target, payload)
    return {"schema_version": 1, "status": "updated", "task_path": target.relative_to(repo_root).as_posix(), "stage": "verification"}


def validate_task(repo_root: Path, task_id: str, phase: str) -> dict[str, Any]:
    if phase not in {"implementation", "close"}:
        raise ValueError(f"unsupported UI validation phase: {phase}")
    target, payload = load_task(repo_root, task_id)
    level = str(payload["ui_level"])
    requirements = level_requirements(level)
    blocking: list[str] = []
    if requirements["requires_ui_contract"]:
        for required in (CONTRACT_PATH, REGISTRY_PATH):
            if not (repo_root / required).is_file():
                blocking.append(f"missing project UI control file: {required.as_posix()}")
    visual_direction = payload.get("visual_direction")
    if not isinstance(visual_direction, dict) or not visual_direction.get("id"):
        blocking.append("missing selected visual direction")
    else:
        try:
            direction = resolve_visual_direction(str(visual_direction["id"]))
            baseline = read_visual_baseline(repo_root)
            baseline_id = str((baseline or {}).get("direction", {}).get("id") or "")
            if baseline_id != direction["id"]:
                blocking.append("project visual baseline is not approved for the selected direction")
        except ValueError as exc:
            blocking.append(str(exc))
    approvals = payload.get("approvals") if isinstance(payload.get("approvals"), dict) else {}
    if requirements["requires_direction_approval"] and approvals.get("visual_direction") != "approved":
        blocking.append("visual direction is not approved")
    if level == "U3" and approvals.get("design_rfc") != "approved":
        blocking.append("U3 design RFC is not approved")
    if phase == "close" and requirements["requires_visual_evidence"]:
        evidence = payload.get("evidence") if isinstance(payload.get("evidence"), dict) else {}
        screenshots = evidence.get("screenshots") if isinstance(evidence.get("screenshots"), list) else []
        accessibility = evidence.get("accessibility_reports") if isinstance(evidence.get("accessibility_reports"), list) else []
        visual_qa = str(evidence.get("visual_qa_report") or "")
        if not screenshots:
            blocking.append("missing browser screenshot evidence")
        if not visual_qa:
            blocking.append("missing Visual QA report")
        if not accessibility:
            blocking.append("missing accessibility evidence")
        for item in [*screenshots, *accessibility, visual_qa]:
            if item and not (repo_root / str(item)).is_file():
                blocking.append(f"recorded UI evidence is missing: {item}")
    return {
        "schema_version": 1,
        "task_path": target.relative_to(repo_root).as_posix(),
        "task_id": str(payload.get("id") or task_id),
        "ui_level": level,
        "phase": phase,
        "passed": not blocking,
        "blocking": blocking,
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Create and validate project-local UI governance artifacts.")
    parser.add_argument("command", choices=["assess", "init", "set-stage", "approve-rfc", "record-evidence", "check", "list-directions"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--task", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--level", choices=UI_LEVELS, default="")
    parser.add_argument("--requested-skill", default="")
    parser.add_argument("--visual-direction", default="")
    parser.add_argument("--stage", choices=TASK_STAGES, default="")
    parser.add_argument("--approval-note", default="")
    parser.add_argument("--screenshot", action="append", default=[])
    parser.add_argument("--visual-qa", default="")
    parser.add_argument("--accessibility-report", action="append", default=[])
    parser.add_argument("--note", default="")
    parser.add_argument("--phase", choices=["implementation", "close"], default="implementation")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    try:
        repo_root = Path(args.repo_root).expanduser().resolve()
        if args.command == "assess":
            if not args.task.strip() or not args.level:
                raise ValueError("assess requires --task and --level after the agent classifies UI impact")
            report = assess(args.task, args.level, args.requested_skill)
        elif args.command == "list-directions":
            registry = load_visual_direction_registry()
            report = {
                "schema_version": registry["schema_version"],
                "fallback_direction_id": registry["fallback_direction_id"],
                "directions": registry["directions"],
            }
        elif args.command == "init":
            if not args.task.strip() or not args.task_id.strip() or not args.level:
                raise ValueError("init requires --task, --task-id, and --level")
            report = initialize_task(
                repo_root,
                args.task_id,
                args.task,
                args.level,
                args.requested_skill,
                args.visual_direction,
                args.approval_note,
            )
        elif args.command == "set-stage":
            if not args.task_id.strip() or not args.stage:
                raise ValueError("set-stage requires --task-id and --stage")
            report = set_stage(repo_root, args.task_id, args.stage, args.approval_note)
        elif args.command == "approve-rfc":
            if not args.task_id.strip():
                raise ValueError("approve-rfc requires --task-id")
            report = approve_rfc(repo_root, args.task_id, args.approval_note)
        elif args.command == "record-evidence":
            if not args.task_id.strip():
                raise ValueError("record-evidence requires --task-id")
            report = record_evidence(
                repo_root,
                args.task_id,
                args.screenshot,
                args.visual_qa,
                args.accessibility_report,
                args.note,
            )
        else:
            if not args.task_id.strip():
                raise ValueError("check requires --task-id")
            report = validate_task(repo_root, args.task_id, args.phase)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for key, value in report.items():
            print(f"{key}={value}")
    if args.command == "check" and not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
