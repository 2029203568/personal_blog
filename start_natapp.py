#!/usr/bin/env python3
"""
跨平台启动：本地博客 + natapp 内网穿透（Windows / Linux / macOS）。

公网: http://se766f84.natappfree.cc
环境变量:
  NATAPP_LOCAL_PORT  本地端口（Linux 默认 8000，Windows 默认 80）
  NATAPP_AUTHTOKEN   natapp 隧道 token
  HOST               uvicorn 监听地址
"""
from __future__ import annotations

import atexit
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
NATAPP_DIR = PROJECT_ROOT / "natapp"
CONFIG_INI = NATAPP_DIR / "config.ini"
CONFIG_EXAMPLE = NATAPP_DIR / "config.ini.example"

IS_LINUX = sys.platform.startswith("linux")
LOCAL_HOST = os.environ.get("HOST", "127.0.0.1")
PUBLIC_URL = "http://se766f84.natappfree.cc"
DEFAULT_AUTHTOKEN = "84da27cada47ec2f"

_processes: list[subprocess.Popen] = []


def default_local_port() -> int:
    if os.environ.get("NATAPP_LOCAL_PORT"):
        return int(os.environ["NATAPP_LOCAL_PORT"])
    return 8000 if IS_LINUX else 80


LOCAL_PORT = default_local_port()


def natapp_binary_names() -> tuple[str, ...]:
    if sys.platform == "win32":
        return ("natapp.exe", "natapp")
    return ("natapp", "natapp.exe")


def ensure_config() -> None:
    NATAPP_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_INI.exists():
        return
    token = os.environ.get("NATAPP_AUTHTOKEN", DEFAULT_AUTHTOKEN)
    if CONFIG_EXAMPLE.exists():
        CONFIG_INI.write_text(
            CONFIG_EXAMPLE.read_text(encoding="utf-8").replace(
                "你的authtoken", token
            ),
            encoding="utf-8",
        )
    else:
        CONFIG_INI.write_text(
            f"[default]\nauthtoken={token}\nlog=stdout\nloglevel=INFO\n",
            encoding="utf-8",
        )


def find_natapp_binary() -> Path | None:
    for name in natapp_binary_names():
        candidate = NATAPP_DIR / name
        if candidate.exists():
            return candidate
    return None


def print_download_help() -> None:
    print("未找到 natapp 客户端，请先下载：")
    if IS_LINUX:
        print("  bash natapp/download_natapp.sh")
        print("  或: curl -fsSL \"https://natapp.cn/get.sh?authtoken=你的token\" | sh")
    elif sys.platform == "win32":
        print("  powershell -ExecutionPolicy Bypass -File natapp/download_natapp.ps1")
    else:
        print("  bash natapp/download_natapp.sh")
    print("  官网: https://natapp.cn/#download")


def stop_all() -> None:
    for proc in _processes:
        if proc.poll() is None:
            proc.terminate()
    for proc in _processes:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def start_uvicorn() -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        LOCAL_HOST,
        "--port",
        str(LOCAL_PORT),
    ]
    print(f"[1/2] 启动网站: http://{LOCAL_HOST}:{LOCAL_PORT}")
    proc = subprocess.Popen(cmd, cwd=BACKEND_DIR)
    _processes.append(proc)
    return proc


def start_natapp(binary: Path) -> subprocess.Popen:
    if not os.access(binary, os.X_OK) and not sys.platform.startswith("win"):
        binary.chmod(binary.stat().st_mode | 0o111)

    cmd = [str(binary.resolve()), "-config", str(CONFIG_INI.resolve())]
    print(f"[2/2] 启动 natapp 隧道 -> {PUBLIC_URL}")
    print(f"      转发到本机 {LOCAL_HOST}:{LOCAL_PORT}，请与 natapp 后台「本地端口」一致")
    proc = subprocess.Popen(cmd, cwd=NATAPP_DIR)
    _processes.append(proc)
    return proc


def wait_for_server(timeout: float = 15.0) -> bool:
    import urllib.error
    import urllib.request

    url = f"http://{LOCAL_HOST}:{LOCAL_PORT}/api/landing"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.5)
    return False


def main() -> None:
    if not BACKEND_DIR.exists():
        raise FileNotFoundError(f"Backend not found: {BACKEND_DIR}")

    ensure_config()
    natapp_bin = find_natapp_binary()
    if natapp_bin is None:
        print_download_help()
        sys.exit(1)

    atexit.register(stop_all)

    def on_signal(*_args: object) -> None:
        stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, on_signal)

    server = start_uvicorn()
    time.sleep(1.5)
    if server.poll() is not None:
        print("网站启动失败。常见原因：")
        print("  1. 未安装依赖: pip install -r backend/requirements.txt")
        if LOCAL_PORT < 1024:
            if IS_LINUX:
                print("  2. 1024 以下端口需 root: sudo -E python3 start_natapp.py")
                print("     或: export NATAPP_LOCAL_PORT=8000 并在 natapp 后台改为 8000")
            else:
                print("  2. 80 端口需管理员权限，或设置 NATAPP_LOCAL_PORT=8000")
        sys.exit(1)

    if not wait_for_server():
        print("警告: 本地服务未在预期时间内就绪，natapp 仍会启动，请查看日志。")

    natapp_proc = start_natapp(natapp_bin)
    print()
    print("=" * 50)
    print(f"  系统: {platform.system()} {platform.machine()}")
    print(f"  本地: http://127.0.0.1:{LOCAL_PORT}")
    print(f"  公网: {PUBLIC_URL}")
    print("  按 Ctrl+C 停止")
    print("=" * 50)
    print()

    try:
        while True:
            if server.poll() is not None:
                print("网站进程已退出")
                break
            if natapp_proc.poll() is not None:
                print(f"natapp 已退出 (code={natapp_proc.returncode})")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_all()


if __name__ == "__main__":
    main()
