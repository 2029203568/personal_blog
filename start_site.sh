#!/usr/bin/env bash
# 一键启动（安装依赖 + 视频准备 + 启动），等价于 python3 start_site.py
set -euo pipefail
cd "$(dirname "$0")"

export HOST="${HOST:-0.0.0.0}"
export PORT="${PORT:-8000}"
export RELOAD="${RELOAD:-0}"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

exec python3 start_site.py "$@"
