"""交付脚本资源清单：源文件 → 站点路径，供 start_site / sync_code 共用。"""
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
CODE_DIR = PROJECT_ROOT / "frontend" / "assets" / "code"

SOURCE_DIRS = [
    PROJECT_ROOT.parent,
    PROJECT_ROOT,
]

# output: frontend/assets/code/ 下的文件名
# sources: 上级目录中可能的源文件名（按优先级）
CODE_CATALOG = [
    {
        "output": "douyin-pinglun-huoke.py",
        "sources": ["抖音评论区获客.py"],
    },
    {
        "output": "douyin-sixin-huoke.py",
        "sources": ["抖音私信获客.py"],
    },
]


def find_source_file(source_names: list[str]) -> Path | None:
    for folder in SOURCE_DIRS:
        if not folder.is_dir():
            continue
        for name in source_names:
            candidate = folder / name
            if candidate.is_file():
                return candidate
    return None


def catalog_output_path(entry: dict) -> Path:
    return CODE_DIR / entry["output"]
