from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from wiki_lib import VAULT_ROOT, iter_markdown_files, load_page


INDEX_SCHEMA_VERSION = 1
DEFAULT_INDEX_PATH = VAULT_ROOT / "00_system" / ".cache" / "retrieval.sqlite3"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class RefreshStats:
    added: int
    updated: int
    deleted: int
    unchanged: int
    indexed_pages: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def resolve_index_path(raw_path: str | Path | None = None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    return DEFAULT_INDEX_PATH


def index_path_label(index_path: Path, *, vault_root: Path = VAULT_ROOT) -> str:
    try:
        return index_path.relative_to(vault_root).as_posix()
    except ValueError:
        return str(index_path)


def connect_index(index_path: str | Path | None = None) -> sqlite3.Connection:
    path = resolve_index_path(index_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    ensure_schema(connection)
    return connection


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE IF NOT EXISTS index_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    row = connection.execute("SELECT value FROM index_meta WHERE key = 'schema_version'").fetchone()
    if row is not None and int(row["value"]) != INDEX_SCHEMA_VERSION:
        reset_schema(connection)

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS pages (
            rel_path TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            body TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            frontmatter_json TEXT NOT NULL,
            project TEXT NOT NULL,
            page_type TEXT NOT NULL,
            domain TEXT NOT NULL,
            status TEXT NOT NULL,
            updated TEXT NOT NULL,
            mtime_ns INTEGER NOT NULL,
            file_size INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chunks (
            chunk_key TEXT PRIMARY KEY,
            rel_path TEXT NOT NULL REFERENCES pages(rel_path) ON DELETE CASCADE,
            ordinal INTEGER NOT NULL,
            heading TEXT NOT NULL,
            body TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_pages_project ON pages(project);
        CREATE INDEX IF NOT EXISTS idx_pages_type ON pages(page_type);
        CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(rel_path, ordinal);

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            chunk_key UNINDEXED,
            rel_path UNINDEXED,
            title,
            heading,
            summary,
            tags,
            body,
            tokenize='trigram'
        );
        """
    )
    connection.execute(
        "INSERT OR REPLACE INTO index_meta(key, value) VALUES('schema_version', ?)",
        (str(INDEX_SCHEMA_VERSION),),
    )
    connection.commit()


def reset_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        DROP TABLE IF EXISTS chunks_fts;
        DROP TABLE IF EXISTS chunks;
        DROP TABLE IF EXISTS pages;
        DELETE FROM index_meta;
        """
    )
    connection.commit()


def split_markdown_chunks(title: str, body: str) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    heading = title
    lines: list[str] = []

    def flush() -> None:
        text = "\n".join(lines).strip()
        if text:
            chunks.append((heading, text))

    for line in body.splitlines():
        match = HEADING_RE.match(line.strip())
        if match:
            flush()
            heading = match.group(2).strip()
            lines = []
            continue
        lines.append(line)
    flush()

    if not chunks:
        chunks.append((title, body.strip()))
    return chunks


def json_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def upsert_page(connection: sqlite3.Connection, path: Path, *, vault_root: Path = VAULT_ROOT) -> None:
    loaded = load_page(path)
    frontmatter = loaded["frontmatter"] if isinstance(loaded["frontmatter"], dict) else {}
    rel_path = path.relative_to(vault_root).as_posix()
    tags = json_list(loaded.get("tags"))
    stat = path.stat()

    connection.execute(
        """
        INSERT INTO pages(
            rel_path, title, summary, body, tags_json, frontmatter_json,
            project, page_type, domain, status, updated, mtime_ns, file_size
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(rel_path) DO UPDATE SET
            title=excluded.title,
            summary=excluded.summary,
            body=excluded.body,
            tags_json=excluded.tags_json,
            frontmatter_json=excluded.frontmatter_json,
            project=excluded.project,
            page_type=excluded.page_type,
            domain=excluded.domain,
            status=excluded.status,
            updated=excluded.updated,
            mtime_ns=excluded.mtime_ns,
            file_size=excluded.file_size
        """,
        (
            rel_path,
            str(loaded["title"]),
            str(loaded["summary"]),
            str(loaded["body"]),
            json.dumps(tags, ensure_ascii=False),
            json.dumps(frontmatter, ensure_ascii=False, default=str),
            str(frontmatter.get("project") or ""),
            str(frontmatter.get("type") or ""),
            str(frontmatter.get("domain") or ""),
            str(frontmatter.get("status") or ""),
            str(frontmatter.get("updated") or ""),
            stat.st_mtime_ns,
            stat.st_size,
        ),
    )
    connection.execute("DELETE FROM chunks_fts WHERE rel_path = ?", (rel_path,))
    connection.execute("DELETE FROM chunks WHERE rel_path = ?", (rel_path,))

    for ordinal, (heading, chunk_body) in enumerate(
        split_markdown_chunks(str(loaded["title"]), str(loaded["body"])),
        start=1,
    ):
        chunk_key = f"{rel_path}::{ordinal}"
        connection.execute(
            "INSERT INTO chunks(chunk_key, rel_path, ordinal, heading, body) VALUES (?, ?, ?, ?, ?)",
            (chunk_key, rel_path, ordinal, heading, chunk_body),
        )
        connection.execute(
            """
            INSERT INTO chunks_fts(chunk_key, rel_path, title, heading, summary, tags, body)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chunk_key,
                rel_path,
                str(loaded["title"]),
                heading,
                str(loaded["summary"]),
                " ".join(tags),
                chunk_body,
            ),
        )


def refresh_index(
    connection: sqlite3.Connection,
    *,
    vault_root: Path = VAULT_ROOT,
    force: bool = False,
) -> RefreshStats:
    existing_rows = connection.execute("SELECT rel_path, mtime_ns, file_size FROM pages").fetchall()
    existing = {str(row["rel_path"]): row for row in existing_rows}
    current_paths: set[str] = set()
    added = 0
    updated = 0
    unchanged = 0

    for path in sorted(iter_markdown_files(), key=lambda item: item.as_posix().lower()):
        rel_path = path.relative_to(vault_root).as_posix()
        current_paths.add(rel_path)
        stat = path.stat()
        previous = existing.get(rel_path)
        changed = (
            force
            or previous is None
            or int(previous["mtime_ns"]) != stat.st_mtime_ns
            or int(previous["file_size"]) != stat.st_size
        )
        if not changed:
            unchanged += 1
            continue
        upsert_page(connection, path, vault_root=vault_root)
        if previous is None:
            added += 1
        else:
            updated += 1

    deleted_paths = sorted(set(existing) - current_paths)
    for rel_path in deleted_paths:
        connection.execute("DELETE FROM chunks_fts WHERE rel_path = ?", (rel_path,))
        connection.execute("DELETE FROM pages WHERE rel_path = ?", (rel_path,))

    connection.commit()
    indexed_pages = int(connection.execute("SELECT COUNT(*) FROM pages").fetchone()[0])
    return RefreshStats(
        added=added,
        updated=updated,
        deleted=len(deleted_paths),
        unchanged=unchanged,
        indexed_pages=indexed_pages,
    )


def indexed_pages(connection: sqlite3.Connection, *, vault_root: Path = VAULT_ROOT) -> list[dict[str, object]]:
    pages: list[dict[str, object]] = []
    for row in connection.execute("SELECT * FROM pages ORDER BY rel_path"):
        try:
            frontmatter = json.loads(str(row["frontmatter_json"]))
        except json.JSONDecodeError:
            frontmatter = {}
        try:
            tags = json.loads(str(row["tags_json"]))
        except json.JSONDecodeError:
            tags = []
        rel_path = str(row["rel_path"])
        pages.append(
            {
                "path": vault_root / Path(rel_path),
                "rel_path": rel_path,
                "source_layer": "raw" if rel_path.startswith("01_inbox/raw/") else "governed",
                "title": str(row["title"]),
                "summary": str(row["summary"]),
                "frontmatter": frontmatter if isinstance(frontmatter, dict) else {},
                "body": str(row["body"]),
                "tags": tags if isinstance(tags, list) else [],
            }
        )
    return pages


def best_chunk(
    connection: sqlite3.Connection,
    rel_path: str,
    query_terms: list[str],
) -> dict[str, object]:
    fts_ranks: dict[str, float] = {}
    fts_terms = [term for term in query_terms if len(term) >= 3]
    if fts_terms:
        fts_query = " OR ".join(f'"{term}"' for term in fts_terms)
        matched_rows = connection.execute(
            """
            SELECT chunks_fts.chunk_key, bm25(chunks_fts) AS rank
            FROM chunks_fts
            WHERE chunks_fts MATCH ? AND chunks_fts.rel_path = ?
            """,
            (fts_query, rel_path),
        ).fetchall()
        fts_ranks = {str(row["chunk_key"]): float(row["rank"]) for row in matched_rows}

    rows = connection.execute(
        "SELECT chunk_key, ordinal, heading, body FROM chunks WHERE rel_path = ? ORDER BY ordinal",
        (rel_path,),
    ).fetchall()
    if not rows:
        return {"heading": "", "body": ""}

    def chunk_score(row: sqlite3.Row) -> tuple[int, int, int, float, int]:
        heading = str(row["heading"]).lower()
        body = str(row["body"]).lower()
        combined = f"{heading}\n{body}"
        coverage = sum(1 for term in query_terms if term in combined)
        heading_hits = sum(1 for term in query_terms if term in heading)
        occurrences = sum(combined.count(term) for term in query_terms)
        fts_rank = -fts_ranks.get(str(row["chunk_key"]), 1_000_000.0)
        return coverage, heading_hits, occurrences, fts_rank, -int(row["ordinal"])

    selected = max(rows, key=chunk_score)
    return {"heading": str(selected["heading"]), "body": str(selected["body"])}
