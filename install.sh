#!/usr/bin/env bash
# Linux / macOS 安装依赖
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 &>/dev/null; then
  echo "请先安装 python3: sudo apt install python3 python3-pip python3-venv"
  exit 1
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install -U pip
pip install -r backend/requirements.txt

echo ""
echo "安装完成。一键启动："
echo "  python3 start_site.py    # 依赖 + 视频 + 启动（推荐）"
echo "  ./start_natapp.sh        # 网站 + natapp 穿透"
