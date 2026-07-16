from __future__ import annotations

import argparse
import json
from contextlib import closing

from retrieval_index import INDEX_SCHEMA_VERSION, connect_index, index_path_label, refresh_index, resolve_index_path


def main() -> None:
    parser = argparse.ArgumentParser(description="构建或增量刷新 ObsidianToWiki 本地检索索引。")
    parser.add_argument("--index-path", default="", help="可选的 SQLite 索引路径")
    parser.add_argument("--full", action="store_true", help="强制重新解析全部 Markdown 页面")
    args = parser.parse_args()

    index_path = resolve_index_path(args.index_path or None)
    with closing(connect_index(index_path)) as connection:
        stats = refresh_index(connection, force=args.full)

    payload = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "backend": "sqlite-fts5",
        "index_path": index_path_label(index_path),
        **stats.to_dict(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
