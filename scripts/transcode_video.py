#!/usr/bin/env python3
"""
将演示 MP4 转为 faststart MP4 + HLS（多码率），供案例页 hls.js 播放。

依赖: ffmpeg（服务器: yum install ffmpeg 或 apt install ffmpeg）

用法:
  python scripts/transcode_video.py
  python scripts/transcode_video.py --input /path/to/facebook养号.mp4 --id facebook-yanghao
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = PROJECT_ROOT / "frontend" / "assets" / "videos"
DEFAULT_INPUT = PROJECT_ROOT.parent / "产品示例视频" / "facebook养号.mp4"
DEFAULT_ID = "facebook-yanghao"

# 720p ~1.5 Mbps，480p ~800 kbps（网页演示够用）
VARIANTS = [
    {
        "name": "720p",
        "scale": "scale=-2:720",
        "bv": "1500k",
        "maxrate": "1800k",
        "bufsize": "3000k",
        "bandwidth": 1800000,
        "resolution": "1280x720",
    },
    {
        "name": "480p",
        "scale": "scale=-2:480",
        "bv": "800k",
        "maxrate": "960k",
        "bufsize": "1600k",
        "bandwidth": 960000,
        "resolution": "854x480",
    },
]

HLS_SEGMENT_SECONDS = 6


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        print("未找到 ffmpeg，请先安装后再运行本脚本。", file=sys.stderr)
        sys.exit(1)
    return path


def transcode_faststart_mp4(ffmpeg: str, src: Path, dest: Path) -> None:
    """H.264/AAC + moov 前置，浏览器可边下边播。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(src),
            "-vf",
            VARIANTS[0]["scale"],
            "-c:v",
            "libx264",
            "-profile:v",
            "main",
            "-level",
            "4.0",
            "-pix_fmt",
            "yuv420p",
            "-b:v",
            VARIANTS[0]["bv"],
            "-maxrate",
            VARIANTS[0]["maxrate"],
            "-bufsize",
            VARIANTS[0]["bufsize"],
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(dest),
        ]
    )


def transcode_hls_variant(ffmpeg: str, src: Path, out_dir: Path, variant: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    segment_pattern = str(out_dir / "seg_%03d.ts")
    playlist = out_dir / "index.m3u8"
    run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(src),
            "-vf",
            variant["scale"],
            "-c:v",
            "libx264",
            "-profile:v",
            "main",
            "-pix_fmt",
            "yuv420p",
            "-b:v",
            variant["bv"],
            "-maxrate",
            variant["maxrate"],
            "-bufsize",
            variant["bufsize"],
            "-g",
            str(HLS_SEGMENT_SECONDS * 24),
            "-keyint_min",
            str(HLS_SEGMENT_SECONDS * 24),
            "-sc_threshold",
            "0",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ac",
            "2",
            "-hls_time",
            str(HLS_SEGMENT_SECONDS),
            "-hls_playlist_type",
            "vod",
            "-hls_segment_filename",
            segment_pattern,
            str(playlist),
        ]
    )


def write_master_playlist(hls_root: Path) -> Path:
    lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
    for variant in VARIANTS:
        lines.append(
            f'#EXT-X-STREAM-INF:BANDWIDTH={variant["bandwidth"]},RESOLUTION={variant["resolution"]}'
        )
        lines.append(f'{variant["name"]}/index.m3u8')
    master = hls_root / "master.m3u8"
    master.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return master


def main() -> None:
    parser = argparse.ArgumentParser(description="MP4 → faststart + HLS")
    parser.add_argument("--input", type=Path, default=None, help="源 MP4")
    parser.add_argument("--id", default=None, help="输出目录名，如 facebook-yanghao")
    parser.add_argument("--all", action="store_true", help="转码 video_assets.VIDEO_CATALOG 中全部带 hls_id 的条目")
    parser.add_argument("--skip-faststart", action="store_true", help="跳过 faststart MP4，仅生成 HLS")
    args = parser.parse_args()

    ffmpeg = require_ffmpeg()

    if args.all:
        sys.path.insert(0, str(PROJECT_ROOT / "backend"))
        from video_assets import VIDEO_CATALOG, catalog_output_path  # noqa: E402

        for entry in VIDEO_CATALOG:
            hls_id = entry.get("hls_id")
            if not hls_id:
                continue
            src = catalog_output_path(entry)
            if not src.is_file():
                print(f"跳过 {entry['output']}（文件不存在）")
                continue
            transcode_one(ffmpeg, src, hls_id, skip_faststart=args.skip_faststart)
        return

    src = (args.input or DEFAULT_INPUT).resolve()
    video_id = args.id or DEFAULT_ID
    if not src.is_file():
        print(f"源文件不存在: {src}", file=sys.stderr)
        sys.exit(1)
    transcode_one(ffmpeg, src, video_id, skip_faststart=args.skip_faststart)


def transcode_one(ffmpeg: str, src: Path, video_id: str, *, skip_faststart: bool = False) -> None:
    mp4_out = VIDEOS_DIR / f"{video_id}.mp4"
    hls_root = VIDEOS_DIR / video_id

    print(f"源: {src}")
    print(f"faststart MP4: {mp4_out}")
    print(f"HLS 目录: {hls_root}")

    if not skip_faststart and src.resolve() != mp4_out.resolve():
        transcode_faststart_mp4(ffmpeg, src, mp4_out)
    elif not skip_faststart and src.resolve() == mp4_out.resolve():
        tmp = mp4_out.with_name(mp4_out.stem + ".faststart.tmp.mp4")
        run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(src),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                "-f",
                "mp4",
                str(tmp),
            ]
        )
        tmp.replace(mp4_out)

    if hls_root.exists():
        shutil.rmtree(hls_root)
    hls_root.mkdir(parents=True)

    for variant in VARIANTS:
        transcode_hls_variant(ffmpeg, src, hls_root / variant["name"], variant)

    master = write_master_playlist(hls_root)
    print(f"完成: {master}")


if __name__ == "__main__":
    main()
