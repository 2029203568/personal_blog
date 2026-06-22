"""演示视频资源清单：源文件 → 站点路径，供 start_site / 转码脚本共用。"""
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
VIDEOS_DIR = PROJECT_ROOT / "frontend" / "assets" / "videos"

SOURCE_DIRS = [
    PROJECT_ROOT.parent / "产品示例视频",
    PROJECT_ROOT / "产品示例视频",
]

# output: frontend/assets/videos/ 下的文件名
# sources: 产品示例视频/ 中可能的源文件名（按优先级）
# hls_id: 非空时 TRANSCODE_HLS=1 会生成 {hls_id}/master.m3u8
VIDEO_CATALOG = [
    {
        "output": "facebook-yanghao.mp4",
        "hls_id": "facebook-yanghao",
        "sources": ["facebook养号.mp4", "facebook-yanghao.mp4"],
    },
    {
        "output": "1688-jingpin-tiaoxuan.mp4",
        "hls_id": "1688-jingpin-tiaoxuan",
        "sources": ["竞品挑选.mp4"],
    },
    {
        "output": "1688-zidong-shangjia.mp4",
        "hls_id": "1688-zidong-shangjia",
        "sources": ["自动上架.mp4"],
    },
    {
        "output": "douyin-pinglun-huoke.mp4",
        "hls_id": "douyin-pinglun-huoke",
        "sources": ["抖音评论区获客.mp4"],
    },
    {
        "output": "douyin-sixin-huoke.mp4",
        "hls_id": "douyin-sixin-huoke",
        "sources": ["抖音私信获客.mp4"],
    },
]

DEPLOY_MARKER = VIDEOS_DIR / ".deploy-ready.json"


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
    return VIDEOS_DIR / entry["output"]


def hls_master_path(entry: dict) -> Path | None:
    hls_id = entry.get("hls_id")
    if not hls_id:
        return None
    return VIDEOS_DIR / hls_id / "master.m3u8"
