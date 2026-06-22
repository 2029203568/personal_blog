#!/usr/bin/env python3
"""读取 progress.json 并输出浏览进度汇总（命令行版）。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from progress_logger import compute_stats, read_progress  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="浏览进度统计")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--limit", type=int, default=10, help="最近记录条数")
    args = parser.parse_args()

    stats = compute_stats()
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0

    print("=== 浏览进度统计 ===")
    print(f"总会话数: {stats['total_sessions']}")
    print(f"平均滚动深度: {stats['avg_scroll_pct']}%")
    print(f"视频完播率: {stats['video_completion_rate']}% "
          f"({stats['video_completed_count']}/{stats['video_started_count']})")
    print()

    if stats.get("by_page"):
        print("按页面:")
        for page, info in stats["by_page"].items():
            print(f"  {page}: {info['sessions']} 次, 平均滚动 {info['avg_scroll_pct']}%")
        print()

    if stats.get("top_sections"):
        print("最常浏览区块:")
        for item in stats["top_sections"][:10]:
            print(f"  {item['section']}: {item['count']}")
        print()

    if stats.get("video_milestones"):
        print("视频里程碑触达:")
        for vid, milestones in stats["video_milestones"].items():
            parts = " / ".join(f"{p}%:{c}" for p, c in sorted(milestones.items(), key=lambda x: int(x[0])))
            print(f"  {vid}: {parts}")
        print()

    records = read_progress(limit=args.limit)
    if records:
        print(f"最近 {len(records)} 条:")
        for rec in reversed(records):
            sections = ", ".join(rec.get("sections_viewed") or []) or "-"
            print(
                f"  [{rec.get('ended_at', rec.get('started_at', ''))}] "
                f"{rec.get('page', rec.get('path'))} "
                f"scroll={rec.get('max_scroll_pct', 0)}% "
                f"sections=[{sections}]"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
