from __future__ import annotations

import argparse

from wiki_lib import append_log


def main() -> None:
    parser = argparse.ArgumentParser(description="向 log.md 追加一条事件记录。")
    parser.add_argument("--kind", required=True, help="事件类型，例如 摄入、查询、项目、体检、更新")
    parser.add_argument("--title", required=True, help="事件标题")
    parser.add_argument("--details", default="", help="补充说明")
    parser.add_argument("--actor", default="agent", help="执行者名称")
    args = parser.parse_args()

    append_log(kind=args.kind, title=args.title, details=args.details, actor=args.actor)
    print(f"已记录: {args.kind} | {args.title}")


if __name__ == "__main__":
    main()
