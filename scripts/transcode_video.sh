#!/usr/bin/env bash
# Linux 一键转码演示视频
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v ffmpeg &>/dev/null; then
  echo "请先安装 ffmpeg: yum install -y ffmpeg  或  apt install -y ffmpeg"
  exit 1
fi
python3 scripts/transcode_video.py "$@"
