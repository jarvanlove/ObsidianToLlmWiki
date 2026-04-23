from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from record_learning_candidate import build_reflection
from wiki_lib import SCRIPT_DIR, VAULT_ROOT, iter_markdown_files, load_page, slugify, write_text


LOG_ENTRY_RE = re.compile(r"^## \[([^\]]+)\] ([^|]+) \| (.+)$", re.MULTILINE)
TOKEN_RE = re.compile(r"[\u4e00-\u9fff]+|[a-z0-9]+")
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "项目",
    "分析",
    "反思",
    "运行",
    "记忆",
    "更新",
    "问题",
    "候选",
    "模式",
}


def latest_health_report() -> Path | None:
    reports = sorted((VAULT_ROOT / "40_outputs" / "analyses").glob("知识库体检-*.md"))
    return reports[-1] if reports else None


def parse_bullet_count(text: str, label: str) -> int:
    pattern = rf"- {re.escape(label)}: (\d+)"
    match = re.search(pattern, text)
    return int(match.group(1)) if match else 0


def candidate_path(title: str) -> Path:
    return VAULT_ROOT / "40_outputs" / "reflections" / f"{slugify(title)}.md"


def existing_candidate_signatures() -> set[str]:
    signatures: set[str] = set()
    reflections_root = VAULT_ROOT / "40_outputs" / "reflections"
    if not reflections_root.exists():
        return signatures
    for path in reflections_root.glob("*.md"):
        page = load_page(path)
        frontmatter = page["frontmatter"]
        if isinstance(frontmatter, dict):
            signature = str(frontmatter.get("candidate_signature") or "").strip()
            if signature:
                signatures.add(signature)
    return signatures


def write_candidate(
    title: str,
    observation: str,
    cause: str,
    improvement: str,
    validation: str,
    tags: list[str],
    *,
    candidate_score: int,
    candidate_signature: str,
    candidate_source: str,
    candidate_risk_level: str,
    candidate_upgrade_mode: str,
    candidate_repeat_count: int,
    candidate_domain: str,
    existing_signatures: set[str],
) -> bool:
    destination = candidate_path(title)
    if destination.exists() or (candidate_signature and candidate_signature in existing_signatures):
        return False
    content = build_reflection(
        title=title,
        project_slug="",
        domain="输出",
        tags=tags,
        summary=f"{title} 的自动发现候选。",
        observation=observation,
        cause=cause,
        improvement=improvement,
        validation=validation,
        candidate_score=candidate_score,
        candidate_signature=candidate_signature,
        candidate_source=candidate_source,
        candidate_risk_level=candidate_risk_level,
        candidate_upgrade_mode=candidate_upgrade_mode,
        candidate_repeat_count=candidate_repeat_count,
        candidate_domain=candidate_domain,
    )
    write_text(destination, content)
    if candidate_signature:
        existing_signatures.add(candidate_signature)
    return True


def discover_from_health_report(existing_signatures: set[str], *, min_score: int) -> int:
    report = latest_health_report()
    if report is None:
        return 0
    text = report.read_text(encoding="utf-8")
    candidates = [
        (
            "体检发现-Schema治理",
            parse_bullet_count(text, "Schema 问题"),
            "最近体检持续发现 schema 问题，说明页面约束或迁移流程仍有缺口。",
            "新类型接入、手工编辑或自动生成页未完全符合 schema。",
            "补齐缺失 frontmatter / 扩充豁免规则 / 增加迁移脚本。",
            "下一次体检中该项应下降到 0。",
            ["governance", "schema", "learning"],
        ),
        (
            "体检发现-死链接治理",
            parse_bullet_count(text, "死链接"),
            "最近体检发现死链接，说明页面演化和链接维护之间存在断裂。",
            "页面改名、路径调整或模糊链接未被自动修复。",
            "增加死链接修复流程与链接重写规则。",
            "下一次体检中死链接数量应下降到 0。",
            ["governance", "links", "learning"],
        ),
        (
            "体检发现-来源未沉淀",
            parse_bullet_count(text, "未沉淀来源"),
            "最近体检发现来源已入库但未沉淀，说明摄入到知识页的转化链路不够稳定。",
            "来源状态机虽存在，但自动回填和人工跟进还不够。",
            "补强来源到分析页/项目页的自动推荐与回写流程。",
            "下一次体检中未沉淀来源应下降到 0。",
            ["ingest", "filing", "learning"],
        ),
    ]

    created = 0
    for title, count, observation, cause, improvement, validation, tags in candidates:
        signature = f"health:{title}"
        score = min(10, count + 5)
        if count > 0 and score >= min_score and write_candidate(
            title,
            observation,
            cause,
            improvement,
            validation,
            tags,
            candidate_score=score,
            candidate_signature=signature,
            candidate_source="health_report",
            candidate_risk_level="medium" if "Schema" in title or "死链接" in title else "low",
            candidate_upgrade_mode="manual" if "Schema" in title or "死链接" in title else "semi_auto",
            candidate_repeat_count=count,
            candidate_domain="governance",
            existing_signatures=existing_signatures,
        ):
            created += 1
    return created


def discover_from_logs(existing_signatures: set[str], *, min_score: int) -> int:
    log_path = VAULT_ROOT / "log.md"
    if not log_path.exists():
        return 0
    text = log_path.read_text(encoding="utf-8")
    entries = [match.groups() for match in LOG_ENTRY_RE.finditer(text)]
    update_titles = [title.strip() for _, kind, title in entries if kind.strip() == "更新"]
    counts = Counter(update_titles)

    created = 0
    for title, count in counts.items():
        if count < 2:
            continue
        candidate_title = f"重复更新模式-{title}"
        observation = f"日志中 `{title}` 已重复出现 {count} 次，说明这一类改动或修复可能正在反复发生。"
        cause = "同类问题缺少稳定模板、共享模式页或自动化支持。"
        improvement = "将该重复改动抽象为共享模式、提示词或脚本能力，减少重复劳动。"
        validation = "后续一段时间内观察同类更新事件是否明显减少。"
        signature = f"log:{slugify(title)}"
        score = min(10, count + 2)
        if score >= min_score and write_candidate(
            candidate_title,
            observation,
            cause,
            improvement,
            validation,
            ["learning", "logs", "repeat"],
            candidate_score=score,
            candidate_signature=signature,
            candidate_source="logs",
            candidate_risk_level="low",
            candidate_upgrade_mode="semi_auto",
            candidate_repeat_count=count,
            candidate_domain="automation",
            existing_signatures=existing_signatures,
        ):
            created += 1
    return created


def discover_from_content_tags(existing_signatures: set[str], *, min_score: int) -> int:
    pages = [load_page(path) for path in iter_markdown_files()]
    shared_pages = []
    content_pages = []
    for page in pages:
        rel_path = str(page["rel_path"])
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        note_type = str(frontmatter.get("type") or "").strip()
        if rel_path.startswith("30_shared/") and note_type in {"模式", "提示词", "工具", "架构"}:
            shared_pages.append(page)
        if rel_path.startswith("40_outputs/analyses/") or rel_path.endswith("project.memory.md") or rel_path.startswith("20_projects/active/"):
            content_pages.append(page)

    shared_tags = {
        str(tag).strip().lower()
        for page in shared_pages
        for tag in page["tags"]
        if str(tag).strip()
    }
    ignore_tags = {"analysis", "learning", "logs", "repeat", "query", "filing"}
    tag_counts: Counter[str] = Counter()
    for page in content_pages:
        for tag in page["tags"]:
            normalized = str(tag).strip().lower()
            if normalized and normalized not in ignore_tags:
                tag_counts[normalized] += 1

    created = 0
    for tag, count in tag_counts.items():
        if count < 2 or tag in shared_tags:
            continue
        title = f"共享缺口-{tag}"
        observation = f"标签 `{tag}` 在项目页、分析页或运行记忆中至少出现了 {count} 次，但共享层还没有对应资产。"
        cause = "同一主题已经在多个场景反复出现，但尚未提升为共享模式、工具说明或提示词。"
        improvement = f"评估是否应为 `{tag}` 创建共享模式页、共享提示词或工具页，减少跨项目重复沉淀。"
        validation = f"创建共享资产后，后续与 `{tag}` 相关的查询和项目沉淀应更多回链到 30_shared。"
        signature = f"tag-gap:{tag}"
        score = min(10, count + 1)
        if score >= min_score and write_candidate(
            title,
            observation,
            cause,
            improvement,
            validation,
            ["learning", "shared-gap", tag],
            candidate_score=score,
            candidate_signature=signature,
            candidate_source="content_tags",
            candidate_risk_level="low",
            candidate_upgrade_mode="semi_auto",
            candidate_repeat_count=count,
            candidate_domain="shared",
            existing_signatures=existing_signatures,
        ):
            created += 1
    return created


def tokenize(text: str) -> set[str]:
    tokens = {token.lower() for token in TOKEN_RE.findall(text.lower())}
    return {token for token in tokens if token and token not in STOPWORDS and len(token) > 1}


def page_signature_text(page: dict[str, object]) -> str:
    body = str(page["body"])[:1200]
    return " ".join(
        [
            str(page["title"]),
            str(page["summary"]),
            " ".join(str(tag) for tag in page["tags"]),
            body,
        ]
    )


def discover_from_similar_content(existing_signatures: set[str], *, min_score: int) -> int:
    pages = [load_page(path) for path in iter_markdown_files()]
    candidates = []
    for page in pages:
        rel_path = str(page["rel_path"])
        frontmatter = page["frontmatter"]
        if not isinstance(frontmatter, dict):
            continue
        note_type = str(frontmatter.get("type") or "").strip()
        if note_type not in {"分析", "反思", "项目运行记忆"}:
            continue
        if not (
            rel_path.startswith("40_outputs/analyses/")
            or rel_path.startswith("40_outputs/reflections/")
            or rel_path.endswith("project.memory.md")
        ):
            continue
        tokens = tokenize(page_signature_text(page))
        if tokens:
            candidates.append((page, tokens))

    created = 0
    seen_signatures: set[str] = set()
    for index, (base_page, base_tokens) in enumerate(candidates):
        cluster = [base_page]
        merged_tokens = set(base_tokens)
        for other_page, other_tokens in candidates[index + 1 :]:
            overlap = base_tokens & other_tokens
            threshold = 3 if len(base_tokens) > 6 and len(other_tokens) > 6 else 2
            if len(overlap) >= threshold:
                cluster.append(other_page)
                merged_tokens |= other_tokens
        if len(cluster) < 2:
            continue

        top_tokens = sorted(merged_tokens)[:3]
        signature = "|".join(top_tokens)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        topic = "-".join(top_tokens)
        title = f"主题聚类-{topic}"
        page_links = "、".join(f"[[{Path(str(page['rel_path'])).with_suffix('').as_posix()}|{page['title']}]]" for page in cluster[:5])
        observation = f"以下页面在标题、摘要或标签层面呈现出明显主题重合：{page_links}。"
        cause = "相似问题已经在多个分析页、反思页或运行记忆中出现，但还没有被抽象成共享资产。"
        improvement = f"围绕主题 `{topic}` 评估是否应创建共享模式、提示词或工具说明，减少未来重复查询和重复沉淀。"
        validation = "创建共享资产后，后续相似页面应更多回链到共享层，而不是继续分散出现。"
        signature = f"cluster:{signature}"
        score = min(10, len(cluster) + 2)
        if score >= min_score and write_candidate(
            title,
            observation,
            cause,
            improvement,
            validation,
            ["learning", "cluster", *top_tokens[:2]],
            candidate_score=score,
            candidate_signature=signature,
            candidate_source="content_cluster",
            candidate_risk_level="medium",
            candidate_upgrade_mode="semi_auto",
            candidate_repeat_count=len(cluster),
            candidate_domain="retrieval",
            existing_signatures=existing_signatures,
        ):
            created += 1
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="从日志和体检报告中自动发现学习候选。")
    parser.add_argument("--rebuild", action="store_true", help="发现候选后重建索引")
    parser.add_argument("--min-score", type=int, default=1, help="只写入不低于该分数的候选")
    args = parser.parse_args()

    existing_signatures = existing_candidate_signatures()
    created = 0
    created += discover_from_health_report(existing_signatures, min_score=args.min_score)
    created += discover_from_logs(existing_signatures, min_score=args.min_score)
    created += discover_from_content_tags(existing_signatures, min_score=args.min_score)
    created += discover_from_similar_content(existing_signatures, min_score=args.min_score)

    if args.rebuild and created:
        subprocess.run([sys.executable, str(SCRIPT_DIR / "rebuild_indexes.py")], check=True)

    print(f"created={created}")


if __name__ == "__main__":
    main()
