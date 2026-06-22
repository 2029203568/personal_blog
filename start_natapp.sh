#!/usr/bin/env bash
# Linux / macOS 启动网站 + natapp
set -euo pipefail
cd "$(dirname "$0")"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export HOST="${HOST:-127.0.0.1}"
export NATAPP_LOCAL_PORT="${NATAPP_LOCAL_PORT:-8000}"

if [ ! -x "natapp/natapp" ] && [ ! -f "natapp/natapp" ]; then
  echo "正在下载 natapp 客户端..."
  bash natapp/download_natapp.sh
fi

exec python3 start_natapp.py
