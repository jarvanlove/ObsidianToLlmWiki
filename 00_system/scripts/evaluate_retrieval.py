from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from retrieval_index import DEFAULT_INDEX_PATH, INDEX_SCHEMA_VERSION, resolve_index_path


SEARCH_SCRIPT = Path(__file__).resolve().with_name("search_wiki.py")


def string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def load_cases(path: Path) -> list[dict[str, object]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read evaluation cases: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise SystemExit("evaluation cases require schema_version=1")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise SystemExit("evaluation cases must contain a non-empty cases list")

    cases: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for index, raw_case in enumerate(raw_cases, start=1):
        if not isinstance(raw_case, dict):
            raise SystemExit(f"evaluation case {index} must be an object")
        case_id = str(raw_case.get("id") or "").strip()
        query = str(raw_case.get("query") or "").strip()
        expected_paths = string_list(raw_case.get("expected_paths"))
        if not case_id or case_id in seen_ids:
            raise SystemExit(f"evaluation case {index} has an empty or duplicate id")
        if not query or not expected_paths:
            raise SystemExit(f"evaluation case {case_id} requires query and expected_paths")
        seen_ids.add(case_id)
        cases.append(raw_case)
    return cases


def run_search(
    case: dict[str, object],
    *,
    index_path: Path,
    refresh: bool,
) -> dict[str, object]:
    max_rank = max(1, int(case.get("max_rank") or 5))
    command = [
        sys.executable,
        str(SEARCH_SCRIPT),
        str(case["query"]),
        "--limit",
        str(max_rank),
        "--format",
        "json",
        "--index-path",
        str(index_path),
        "--no-log-failures",
    ]
    filters = case.get("filters") if isinstance(case.get("filters"), dict) else {}
    for key in ("project", "type", "tag"):
        value = str(filters.get(key) or "").strip()
        if value:
            command.extend([f"--{key}", value])
    if not refresh:
        command.append("--no-refresh")

    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=child_env,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"search failed with exit code {completed.returncode}")
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("search returned a non-object JSON payload")
    return payload


def evaluate_case(case: dict[str, object], payload: dict[str, object]) -> dict[str, object]:
    expected_paths = string_list(case.get("expected_paths"))
    expected_headings = string_list(case.get("expected_headings"))
    max_rank = max(1, int(case.get("max_rank") or 5))
    results = payload.get("results") if isinstance(payload.get("results"), list) else []

    matched: dict[str, object] | None = None
    for item in results:
        if isinstance(item, dict) and str(item.get("path") or "") in expected_paths:
            matched = item
            break

    rank = int(matched.get("rank") or 0) if matched else 0
    path_hit = bool(matched and 0 < rank <= max_rank)
    actual_heading = str(matched.get("heading") or "") if matched else ""
    heading_hit = not expected_headings or any(
        expected.lower() in actual_heading.lower() for expected in expected_headings
    )
    require_source_refs = bool(case.get("require_source_refs", False))
    source_refs = matched.get("source_refs") if matched and isinstance(matched.get("source_refs"), list) else []
    provenance_hit = not require_source_refs or bool(source_refs)
    passed = path_hit and heading_hit and provenance_hit

    return {
        "id": str(case["id"]),
        "query": str(case["query"]),
        "gating": bool(case.get("gating", True)),
        "semantic_probe": bool(case.get("semantic_probe", False)),
        "passed": passed,
        "path_hit": path_hit,
        "heading_hit": heading_hit,
        "provenance_hit": provenance_hit,
        "expected_paths": expected_paths,
        "matched_path": str(matched.get("path") or "") if matched else "",
        "rank": rank,
        "reciprocal_rank": 1.0 / rank if path_hit else 0.0,
        "expected_headings": expected_headings,
        "matched_heading": actual_heading,
        "source_refs": source_refs,
    }


def rounded_ratio(numerator: int | float, denominator: int) -> float:
    return round(float(numerator) / denominator, 4) if denominator else 0.0


def render_text(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "Retrieval Evaluation",
        f"gate_passed={str(payload['gate_passed']).lower()}",
        f"gating_pass_rate={summary['gating_pass_rate']:.4f}",
        f"mrr={summary['mrr']:.4f}",
        f"semantic_probe_pass_rate={summary['semantic_probe_pass_rate']:.4f}",
        f"semantic_retrieval_recommended={str(payload['semantic_retrieval_recommended']).lower()}",
        "",
    ]
    for item in payload["cases"]:
        state = "PASS" if item["passed"] else "FAIL"
        lines.append(
            f"[{state}] {item['id']} rank={item['rank'] or '-'} path={item['matched_path'] or '-'} heading={item['matched_heading'] or '-'}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="运行可重复的 ObsidianToWiki 检索质量评测。")
    parser.add_argument("--cases", required=True, help="schema_version=1 的评测用例 JSON")
    parser.add_argument("--index-path", default=str(DEFAULT_INDEX_PATH), help="可选 SQLite 索引路径")
    parser.add_argument("--minimum-pass-rate", type=float, default=1.0, help="门禁用例最低通过率")
    parser.add_argument("--minimum-mrr", type=float, default=0.8, help="门禁用例最低 MRR")
    parser.add_argument("--semantic-probe-threshold", type=float, default=0.8, help="低于此探针通过率时建议语义检索")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    args = parser.parse_args()

    cases = load_cases(Path(args.cases).expanduser().resolve())
    index_path = resolve_index_path(args.index_path)
    evaluations: list[dict[str, object]] = []
    for index, case in enumerate(cases):
        try:
            search_payload = run_search(case, index_path=index_path, refresh=index == 0)
            evaluations.append(evaluate_case(case, search_payload))
        except (RuntimeError, json.JSONDecodeError) as exc:
            evaluations.append(
                {
                    "id": str(case["id"]),
                    "query": str(case["query"]),
                    "gating": bool(case.get("gating", True)),
                    "semantic_probe": bool(case.get("semantic_probe", False)),
                    "passed": False,
                    "path_hit": False,
                    "heading_hit": False,
                    "provenance_hit": False,
                    "expected_paths": string_list(case.get("expected_paths")),
                    "matched_path": "",
                    "rank": 0,
                    "reciprocal_rank": 0.0,
                    "expected_headings": string_list(case.get("expected_headings")),
                    "matched_heading": "",
                    "source_refs": [],
                    "error": str(exc),
                }
            )

    gating = [item for item in evaluations if item["gating"]]
    probes = [item for item in evaluations if item["semantic_probe"]]
    gating_pass_rate = rounded_ratio(sum(1 for item in gating if item["passed"]), len(gating))
    mrr = rounded_ratio(sum(float(item["reciprocal_rank"]) for item in gating), len(gating))
    probe_pass_rate = rounded_ratio(sum(1 for item in probes if item["passed"]), len(probes))
    gate_passed = bool(gating) and gating_pass_rate >= args.minimum_pass_rate and mrr >= args.minimum_mrr
    semantic_recommended = bool(probes) and probe_pass_rate < args.semantic_probe_threshold

    payload = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "gate_passed": gate_passed,
        "semantic_retrieval_recommended": semantic_recommended,
        "thresholds": {
            "minimum_pass_rate": args.minimum_pass_rate,
            "minimum_mrr": args.minimum_mrr,
            "semantic_probe_threshold": args.semantic_probe_threshold,
        },
        "summary": {
            "total": len(evaluations),
            "gating_total": len(gating),
            "gating_pass_rate": gating_pass_rate,
            "mrr": mrr,
            "semantic_probe_total": len(probes),
            "semantic_probe_pass_rate": probe_pass_rate,
        },
        "cases": evaluations,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else render_text(payload))
    raise SystemExit(0 if gate_passed else 1)


if __name__ == "__main__":
    main()
