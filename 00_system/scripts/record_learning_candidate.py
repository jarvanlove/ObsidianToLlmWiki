from __future__ import annotations

import argparse
import subprocess
import sys

from create_page import ensure_project
from wiki_lib import SCRIPT_DIR, VAULT_ROOT, append_log, normalize_tags, render_markdown, slugify, today_iso, write_text


def build_reflection(
    *,
    title: str,
    project_slug: str,
    domain: str,
    tags: list[str],
    summary: str,
    observation: str,
    cause: str,
    improvement: str,
    validation: str,
    candidate_score: int = 1,
    candidate_signature: str = "",
    candidate_source: str = "manual",
    promoted_to: str = "",
) -> str:
    frontmatter = {
        "title": title,
        "type": "反思",
        "domain": domain,
        "project": project_slug,
        "status": "候选",
        "tags": tags,
        "updated": today_iso(),
        "summary": summary,
        "candidate_score": candidate_score,
        "candidate_signature": candidate_signature,
        "candidate_source": candidate_source,
        "promoted_to": promoted_to,
    }
    body = "\n".join(
        [
            f"# {title}",
            "",
            "## 观察",
            "",
            observation.strip() or "- ",
            "",
            "## 原因分析",
            "",
            cause.strip() or "- ",
            "",
            "## 候选改进",
            "",
            improvement.strip() or "- ",
            "",
            "## 后续验证",
            "",
            validation.strip() or "- ",
        ]
    )
    return render_markdown(frontmatter, body)


def main() -> None:
    parser = argparse.ArgumentParser(description="记录一个学习候选或系统反思。")
    parser.add_argument("--title", required=True, help="反思标题")
    parser.add_argument("--observation", required=True, help="观察")
    parser.add_argument("--cause", default="", help="原因分析")
    parser.add_argument("--improvement", default="", help="候选改进")
    parser.add_argument("--validation", default="", help="后续验证")
    parser.add_argument("--project", default="", help="所属项目名")
    parser.add_argument("--tags", default="", help="英文逗号分隔标签")
    parser.add_argument("--summary", default="", help="一句话摘要")
    parser.add_argument("--candidate-score", type=int, default=1, help="候选成熟度分数")
    parser.add_argument("--candidate-signature", default="", help="候选去重签名")
    parser.add_argument("--candidate-source", default="manual", help="候选来源")
    args = parser.parse_args()

    title = args.title.strip()
    project_name = args.project.strip()
    project_slug = slugify(project_name) if project_name else ""
    tags = normalize_tags(args.tags)
    summary = args.summary.strip() or f"{title} 的学习候选。"

    if project_name:
        root = ensure_project(project_name, tags=[], status="活跃", summary=f"{project_name} 的项目知识库。")
        destination = root / "notes" / f"{slugify(title)}.md"
        domain = "项目"
    else:
        destination = VAULT_ROOT / "40_outputs" / "reflections" / f"{slugify(title)}.md"
        domain = "输出"

    content = build_reflection(
        title=title,
        project_slug=project_slug,
        domain=domain,
        tags=tags,
        summary=summary,
        observation=args.observation,
        cause=args.cause,
        improvement=args.improvement,
        validation=args.validation,
        candidate_score=args.candidate_score,
        candidate_signature=args.candidate_signature,
        candidate_source=args.candidate_source,
    )
    write_text(destination, content)
    append_log("更新", title, f"已记录学习候选到 {destination.relative_to(VAULT_ROOT).as_posix()}")
    subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)
    print(destination)


if __name__ == "__main__":
    main()
