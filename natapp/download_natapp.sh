#!/usr/bin/env bash
# Linux / macOS 下载 natapp 客户端
set -euo pipefail
cd "$(dirname "$0")"

TOKEN="${NATAPP_AUTHTOKEN:-84da27cada47ec2f}"

echo "正在下载 natapp 到 $(pwd) ..."
curl -fsSL "https://natapp.cn/get.sh?authtoken=${TOKEN}" | sh

if [ -f "natapp" ]; then
  chmod +x natapp
  echo "完成: $(pwd)/natapp"
elif [ -f "run_natapp.sh" ] || [ -f "run_natapp.bat" ]; then
  echo "安装脚本已执行，请查看当前目录下的 natapp 或 run_natapp 脚本"
else
  echo "若未自动下载，请访问 https://natapp.cn/#download 手动下载 Linux 版"
fi
