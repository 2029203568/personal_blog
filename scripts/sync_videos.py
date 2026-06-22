#!/usr/bin/env python3
"""将 产品示例视频/ 中的演示 MP4 同步到 frontend/assets/videos/。"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from video_assets import VIDEO_CATALOG, VIDEOS_DIR, catalog_output_path, find_source_file  # noqa: E402
from asset_sync import write_sync_report  # noqa: E402


def main() -> None:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    for entry in VIDEO_CATALOG:
        output = catalog_output_path(entry)
        source = find_source_file(entry["sources"])
        if not source:
            print(f"跳过 {entry['output']}（未找到源: {', '.join(entry['sources'])}）")
            continue
        if output.is_file() and output.stat().st_mtime >= source.stat().st_mtime:
            print(f"已是最新 {output.name}")
            continue
        print(f"复制 {source.name} → {output.name}")
        shutil.copy2(source, output)
        copied += 1
    print(f"\n完成，本次更新 {copied} 个文件。目录: {VIDEOS_DIR}")
    report = write_sync_report()
    print(f"资源同步记录: {report}")


if __name__ == "__main__":
    main()
