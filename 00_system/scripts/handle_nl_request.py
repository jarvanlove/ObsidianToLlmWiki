from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from wiki_lib import normalize_tags


SCRIPT_DIR = Path(__file__).resolve().parent


def load_project_context(repo_root: Path) -> dict[str, object]:
    context_path = repo_root / "wiki.context.json"
    if not context_path.exists():
        return {}
    try:
        payload = json.loads(context_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_project_name(wiki_root: Path, project_slug: str) -> str:
    registry_path = wiki_root / "00_system" / "registry" / "projects.json"
    if not registry_path.exists():
        return project_slug
    try:
        items = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return project_slug
    if not isinstance(items, list):
        return project_slug
    for item in items:
        if not isinstance(item, dict):
            continue
        if str(item.get("project_slug") or "").strip() == project_slug:
            project_name = str(item.get("project_name") or "").strip()
            if project_name:
                return project_name
    return project_slug


def run_python(script_name: str, args: list[str], env: dict[str, str] | None = None) -> None:
    subprocess.run([sys.executable, str(SCRIPT_DIR / script_name), *args], check=True, env=env)


def load_required_project_context(repo_root: Path) -> tuple[dict[str, object], Path, str, str]:
    context = load_project_context(repo_root)
    if not context:
        raise SystemExit("当前项目尚未接入 wiki，请先执行“帮我接入 wiki”。")

    wiki_root = Path(str(context.get("wiki_root") or "")).expanduser().resolve()
    project_slug = str(context.get("project_slug") or "").strip()
    if not project_slug:
        raise SystemExit("wiki.context.json 缺少 project_slug")
    project_name = load_project_name(wiki_root, project_slug)
    return context, wiki_root, project_slug, project_name


def classify_request(text: str) -> str:
    lowered = text.strip().lower()
    compact = lowered.replace(" ", "")

    if "接入wiki" in compact or "接入 wiki" in lowered:
        return "attach_project"
    if "基于当前项目wiki回答" in compact or "当前项目wiki回答" in compact or "基于当前项目 wiki 回答" in lowered:
        return "answer_project"
    if "边开发边沉淀" in compact:
        return "develop_and_file_back"
    if "个人知识库" in compact and any(token in compact for token in ("收进", "摄入", "导入")):
        return "ingest_personal"
    if any(token in compact for token in ("当前项目", "项目里", "项目中")) and any(token in compact for token in ("收进", "摄入", "导入")):
        return "ingest_project"
    if any(token in compact for token in ("记下来", "写回", "沉淀")) and "结论" in compact:
        return "file_back"
    raise SystemExit(f"暂不支持的自然语言请求: {text}")


def infer_file_back_destination(text: str, has_project_context: bool) -> str:
    compact = text.strip().lower().replace(" ", "")

    if any(token in compact for token in ("个人知识", "个人知识库", "个人wiki", "我的个人wiki")):
        return "personal"
    if any(token in compact for token in ("共享知识", "共享层", "共享wiki")):
        return "shared"
    if any(token in compact for token in ("输出页", "分析页", "outputs")):
        return "outputs"
    if any(token in compact for token in ("项目wiki", "项目知识", "项目层")):
        return "project"
    return "project" if has_project_context else "outputs"


def handle_attach_project(repo_root: Path, request: str, tags: str, wiki_root_arg: str) -> None:
    project_name = repo_root.name
    args = ["--repo-root", str(repo_root), "--project", project_name]
    if tags.strip():
        args.extend(["--tags", tags.strip()])
    if wiki_root_arg.strip():
        args.extend(["--wiki-root", wiki_root_arg.strip()])
    run_python("attach_project.py", args)


def handle_ingest_personal(source: str, title: str, tags: str) -> None:
    if not source.strip():
        raise SystemExit("个人知识摄入需要提供 --source")
    inferred_title = title.strip() or Path(source).stem
    args = ["--source", source, "--title", inferred_title]
    if tags.strip():
        args.extend(["--tags", tags.strip()])
    run_python("ingest_source.py", args)


def handle_ingest_project(repo_root: Path, source: str, title: str, tags: str) -> None:
    if not source.strip():
        raise SystemExit("项目知识摄入需要提供 --source")
    _context, wiki_root, _project_slug, project_name = load_required_project_context(repo_root)
    inferred_title = title.strip() or Path(source).stem

    env = dict(os.environ)
    env["OBSIDIAN_WIKI_ROOT"] = str(wiki_root)
    args = ["--source", source, "--title", inferred_title, "--project", project_name]
    if tags.strip():
        args.extend(["--tags", tags.strip()])
    run_python("ingest_source.py", args, env=env)


def handle_file_back(repo_root: Path, request: str, title: str, question: str, conclusion: str, tags: str) -> None:
    if not title.strip() or not question.strip() or not conclusion.strip():
        raise SystemExit("写回结论需要提供 --title、--question、--conclusion")

    args = ["--title", title.strip(), "--question", question.strip(), "--conclusion", conclusion.strip()]
    if tags.strip():
        args.extend(["--tags", tags.strip()])

    context = load_project_context(repo_root)
    destination = infer_file_back_destination(request, has_project_context=bool(context))
    args.extend(["--destination", destination])
    if context:
        _context, wiki_root, _project_slug, project_name = load_required_project_context(repo_root)
        if project_name and destination == "project":
            args.extend(["--project", project_name])
        elif project_name:
            args.extend(["--project", project_name])
        env = dict(os.environ)
        env["OBSIDIAN_WIKI_ROOT"] = str(wiki_root)
        run_python("file_back_query.py", args, env=env)
        return

    run_python("file_back_query.py", args)


def handle_answer_project(repo_root: Path, question: str) -> None:
    if not question.strip():
        raise SystemExit("基于当前项目 wiki 回答需要提供 --question")
    _context, wiki_root, project_slug, _project_name = load_required_project_context(repo_root)
    env = dict(os.environ)
    env["OBSIDIAN_WIKI_ROOT"] = str(wiki_root)
    run_python(
        "search_wiki.py",
        [question.strip(), "--project", project_slug, "--show-relations"],
        env=env,
    )


def handle_develop_and_file_back(repo_root: Path) -> None:
    context, wiki_root, _project_slug, _project_name = load_required_project_context(repo_root)
    read_first = [
        str(wiki_root / str(context.get("project_index") or "")).replace("\\", "/"),
        str(wiki_root / str(context.get("project_memory") or "")).replace("\\", "/"),
        str(wiki_root / str(context.get("project_tasks") or "")).replace("\\", "/"),
    ]
    write_back = [
        str(wiki_root / str(context.get("project_overview") or "")).replace("\\", "/"),
        str(wiki_root / str(context.get("project_architecture") or "")).replace("\\", "/"),
        str(wiki_root / str(context.get("project_decisions") or "")).replace("\\", "/"),
        str(wiki_root / str(context.get("project_tasks") or "")).replace("\\", "/"),
        str(wiki_root / str(context.get("project_sources") or "")).replace("\\", "/"),
    ]
    print("当前项目已接入 wiki。")
    print("开始前先读：")
    for item in read_first:
        print(f"- {item}")
    print("开发后优先回写：")
    for item in write_back:
        print(f"- {item}")
    print("规则：")
    print("- 新资料先摄入项目来源层")
    print("- 稳定结论写回项目 wiki")
    print("- 可复用经验提升到 30_shared")


def main() -> None:
    parser = argparse.ArgumentParser(description="把常见自然语言请求分发到现有 wiki 脚本。")
    parser.add_argument("--request", required=True, help="自然语言请求，例如 帮我接入 wiki")
    parser.add_argument("--repo-root", default=".", help="项目仓库根目录，默认当前目录")
    parser.add_argument("--wiki-root", default="", help="可选，显式指定中心 wiki 根目录")
    parser.add_argument("--source", default="", help="资料路径")
    parser.add_argument("--title", default="", help="标题")
    parser.add_argument("--question", default="", help="问题")
    parser.add_argument("--conclusion", default="", help="结论")
    parser.add_argument("--tags", default="", help="英文逗号分隔标签")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    request_kind = classify_request(args.request)
    tags = ",".join(normalize_tags(args.tags))

    if request_kind == "attach_project":
        handle_attach_project(repo_root, args.request, tags, args.wiki_root)
        return
    if request_kind == "answer_project":
        handle_answer_project(repo_root, args.question)
        return
    if request_kind == "develop_and_file_back":
        handle_develop_and_file_back(repo_root)
        return
    if request_kind == "ingest_personal":
        handle_ingest_personal(args.source, args.title, tags)
        return
    if request_kind == "ingest_project":
        handle_ingest_project(repo_root, args.source, args.title, tags)
        return
    if request_kind == "file_back":
        handle_file_back(repo_root, args.request, args.title, args.question, args.conclusion, tags)
        return

    raise SystemExit(f"未处理的请求类型: {request_kind}")


if __name__ == "__main__":
    main()
