#!/usr/bin/env python3
"""仅将 MP4 moov 移到文件头（-c copy），不重新编码，秒级完成，支持拖拽进度。"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IN = PROJECT_ROOT / "frontend" / "assets" / "videos" / "facebook-yanghao.mp4"
DEFAULT_OUT = DEFAULT_IN


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_IN)
    parser.add_argument("--output", type=Path, default=None, help="默认覆盖输入（先写临时文件）")
    args = parser.parse_args()

    src = args.input.resolve()
    if not src.is_file():
        print(f"文件不存在: {src}", file=sys.stderr)
        sys.exit(1)
    if not shutil.which("ffmpeg"):
        print("需要 ffmpeg", file=sys.stderr)
        sys.exit(1)

    out = (args.output or src).resolve()
    # ffmpeg 3.x 需 .mp4 后缀才能识别输出格式
    tmp = out.with_name(out.stem + ".faststart.tmp.mp4")

    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-c", "copy", "-movflags", "+faststart",
        "-f", "mp4",
        str(tmp),
    ]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)
    tmp.replace(out)
    print(f"完成: {out}")
    print("验证: python3 scripts/check_video_streaming.py")


if __name__ == "__main__":
    main()
