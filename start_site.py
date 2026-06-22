#!/usr/bin/env python3
"""
一键安装依赖、准备演示视频、启动网站（Windows / Linux / macOS）。

环境变量:
  HOST              监听地址，Linux 默认 0.0.0.0，Windows 默认 127.0.0.1
  PORT              端口，默认 8000
  RELOAD            热重载 1/0，Linux 生产默认 0
  SKIP_DEPS         1 跳过 pip 安装
  SKIP_VIDEO_SETUP  1 跳过视频复制/转码
  TRANSCODE_HLS     1 强制完整 HLS 转码（耗时，首次部署可选）
  CREATE_VENV       1 Linux 下若无 .venv 则自动创建
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"
REQUIREMENTS_PY37 = BACKEND_DIR / "requirements-py37.txt"


def resolve_requirements() -> Path:
    if sys.version_info < (3, 8) and REQUIREMENTS_PY37.is_file():
        return REQUIREMENTS_PY37
    return REQUIREMENTS

sys.path.insert(0, str(BACKEND_DIR))
from code_assets import CODE_CATALOG as CODE_CATALOG  # noqa: E402
from code_assets import catalog_output_path as code_output_path  # noqa: E402
from code_assets import find_source_file as find_code_source  # noqa: E402
from video_assets import (  # noqa: E402
    DEPLOY_MARKER,
    VIDEO_CATALOG,
    catalog_output_path,
    find_source_file,
    hls_master_path,
)
from asset_sync import write_sync_report  # noqa: E402

IS_LINUX = sys.platform.startswith("linux")
DEFAULT_HOST = "0.0.0.0" if IS_LINUX else "127.0.0.1"
DEFAULT_PORT = "8000"
DEFAULT_RELOAD = "0" if os.environ.get("RELOAD") is None and IS_LINUX else "1"


def resolve_python() -> str:
    if sys.platform == "win32":
        venv_py = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        venv_py = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_py.is_file():
        return str(venv_py)
    return sys.executable


def ensure_venv() -> str:
    py = resolve_python()
    if py != sys.executable:
        return py
    if os.environ.get("CREATE_VENV") != "1" and not IS_LINUX:
        return py
    venv_dir = PROJECT_ROOT / ".venv"
    if venv_dir.exists():
        return resolve_python()
    if os.environ.get("CREATE_VENV") != "1":
        return py
    print("[1/4] 创建虚拟环境 .venv …")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    return resolve_python()


def run_cmd(py: str, args: list[str], *, cwd: Path | None = None) -> None:
    print("+", " ".join([py, *args]))
    subprocess.run([py, *args], cwd=str(cwd or PROJECT_ROOT), check=True)


def deps_installed(py: str) -> bool:
    r = subprocess.run(
        [py, "-c", "import uvicorn, fastapi, pydantic, typing_extensions"],
        capture_output=True,
    )
    return r.returncode == 0


def ssl_available(py: str) -> bool:
    r = subprocess.run([py, "-c", "import ssl"], capture_output=True)
    return r.returncode == 0


def print_ssl_fix(py: str) -> None:
    print(
        f"错误: {py} 缺少 SSL 模块（No module named '_ssl'）。\n"
        "\n"
        "说明: 网站本身已是 HTTP 启动（http://IP:8000），与 HTTPS 无关。\n"
        "但 uvicorn / pip 启动时都会 import ssl，缺 _ssl 则无法运行，改启动脚本解决不了。\n"
        "\n"
        "宝塔修复步骤：\n"
        "  1. SSH 安装编译依赖（Alibaba Cloud Linux / CentOS）：\n"
        "     yum install -y openssl openssl-devel libffi-devel bzip2-devel zlib-devel "
        "readline-devel sqlite-devel xz-devel tk-devel\n"
        "  2. 宝塔 → 软件商店 → Python 管理器 → 卸载 3.10 → 重新安装 3.10\n"
        "  3. Python 项目 → 运行版本选刚装好的 3.10\n"
        "  4. 验证: python -c \"import ssl; print(ssl.OPENSSL_VERSION)\"\n"
        "  5. pip install -r backend/requirements.txt && python start_site.py\n"
        "\n"
        "若宝塔 Python 仍缺 SSL，可尝试系统 Python：\n"
        "  /usr/bin/python3 -c \"import ssl; print(ssl.OPENSSL_VERSION)\""
    )


def require_ssl(py: str) -> None:
    if ssl_available(py):
        return
    print_ssl_fix(py)
    sys.exit(1)


def ensure_dependencies(py: str) -> None:
    if os.environ.get("SKIP_DEPS") == "1":
        if not deps_installed(py):
            print("错误: 已设置 SKIP_DEPS=1，但当前 Python 缺少 uvicorn/fastapi 等依赖。")
            sys.exit(1)
        print("[2/4] 依赖已就绪（SKIP_DEPS）")
        return
    if deps_installed(py):
        print("[2/4] 依赖已就绪")
        return
    require_ssl(py)
    req = resolve_requirements()
    print("[2/4] 安装 Python 依赖 …")
    if req != REQUIREMENTS:
        print(f"  → 使用 {req.name}（Python 3.7 兼容）")
    subprocess.run([py, "-m", "pip", "install", "-U", "pip"], check=False)
    run_cmd(py, ["-m", "pip", "install", "-r", str(req)])


def load_marker() -> dict:
    if not DEPLOY_MARKER.is_file():
        return {}
    try:
        return json.loads(DEPLOY_MARKER.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_marker(state: dict) -> None:
    DEPLOY_MARKER.parent.mkdir(parents=True, exist_ok=True)
    DEPLOY_MARKER.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def file_fingerprint(path: Path) -> dict:
    stat = path.stat()
    return {"mtime": stat.st_mtime, "size": stat.st_size}


def entry_needs_faststart(output: Path, marker: dict) -> bool:
    if not output.is_file():
        return False
    key = output.name
    saved = marker.get(key)
    if not saved:
        return True
    fp = file_fingerprint(output)
    return saved.get("mtime") != fp["mtime"] or saved.get("size") != fp["size"]


def sync_catalog_file(entry: dict, *, find_source=find_source_file, output_path=catalog_output_path) -> Path | None:
    output = output_path(entry)
    source = find_source(entry["sources"])
    output.parent.mkdir(parents=True, exist_ok=True)

    if not output.is_file():
        if source:
            print(f"  复制 {source.name} → {output.name}")
            shutil.copy2(source, output)
            return output
        print(f"  跳过 {output.name}（源文件未找到: {', '.join(entry['sources'])}）")
        return None

    if source and source.stat().st_mtime > output.stat().st_mtime:
        print(f"  更新 {output.name} ← {source.name}")
        shutil.copy2(source, output)
    return output


def faststart_one(py: str, mp4: Path) -> bool:
    try:
        run_cmd(
            py,
            [
                str(PROJECT_ROOT / "scripts" / "faststart_mp4.py"),
                "--input",
                str(mp4),
            ],
        )
        return True
    except subprocess.CalledProcessError:
        print(f"  警告: faststart 失败，跳过 {mp4.name}（网站仍会启动）")
        return False


def transcode_hls_one(py: str, mp4: Path, hls_id: str) -> None:
    run_cmd(
        py,
        [
            str(PROJECT_ROOT / "scripts" / "transcode_video.py"),
            "--input",
            str(mp4),
            "--id",
            hls_id,
        ],
    )


def ensure_video_assets(py: str) -> None:
    if os.environ.get("SKIP_VIDEO_SETUP") == "1":
        print("[3/4] 跳过视频准备 (SKIP_VIDEO_SETUP=1)")
        report = write_sync_report()
        print(f"  → 已更新资源同步记录: {report.relative_to(PROJECT_ROOT)}")
        return

    print("[3/4] 准备演示视频与交付脚本 …")
    marker = load_marker()
    new_marker = dict(marker)
    has_ffmpeg = bool(shutil.which("ffmpeg"))
    force_hls = os.environ.get("TRANSCODE_HLS") == "1"
    auto_hls = os.environ.get("AUTO_HLS") == "1" and IS_LINUX
    pending_faststart: list[Path] = []

    try:
        for entry in CODE_CATALOG:
            sync_catalog_file(entry, find_source=find_code_source, output_path=code_output_path)

        for entry in VIDEO_CATALOG:
            output = sync_catalog_file(entry)
            if output is None:
                continue
            if entry_needs_faststart(output, marker):
                pending_faststart.append(output)

        if not has_ffmpeg:
            print("  未安装 ffmpeg，跳过 faststart/HLS（建议: yum install -y ffmpeg）")
            for entry in VIDEO_CATALOG:
                output = catalog_output_path(entry)
                if output.is_file():
                    new_marker[output.name] = file_fingerprint(output)
            save_marker(new_marker)
            return

        if force_hls or auto_hls:
            for entry in VIDEO_CATALOG:
                output = catalog_output_path(entry)
                hls_id = entry.get("hls_id")
                if not output.is_file() or not hls_id:
                    continue
                master = hls_master_path(entry)
                if force_hls or not master or not master.is_file():
                    print(f"  HLS 转码 {output.name} …")
                    transcode_hls_one(py, output, hls_id)
                    new_marker[output.name] = {**file_fingerprint(output), "hls": True}
            save_marker(new_marker)
            print("[3/4] 演示视频已就绪（含 HLS）")
            return

        for mp4 in pending_faststart:
            print(f"  faststart {mp4.name} …")
            if faststart_one(py, mp4):
                new_marker[mp4.name] = file_fingerprint(mp4)

        for entry in VIDEO_CATALOG:
            output = catalog_output_path(entry)
            if output.is_file() and output.name not in new_marker:
                new_marker[output.name] = file_fingerprint(output)

        save_marker(new_marker)
        missing = [
            entry["output"]
            for entry in VIDEO_CATALOG
            if not catalog_output_path(entry).is_file()
        ]
        if missing:
            print(f"  警告: 以下演示视频未就绪（请检查 产品示例视频/ 源文件）: {', '.join(missing)}")
        if pending_faststart:
            print("[3/4] 演示视频 faststart 完成")
        else:
            print("[3/4] 演示视频已就绪")
    finally:
        report = write_sync_report()
        print(f"  → 资源同步记录: {report.relative_to(PROJECT_ROOT)}")


def start_server(py: str) -> None:
    require_ssl(py)
    host = os.environ.get("HOST", DEFAULT_HOST)
    port = os.environ.get("PORT", os.environ.get("NATAPP_LOCAL_PORT", DEFAULT_PORT))
    reload = os.environ.get("RELOAD", DEFAULT_RELOAD) == "1"

    cmd = [py, "-m", "uvicorn", "main:app", "--host", host, "--port", port]
    if reload:
        cmd.append("--reload")

    url_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    print("[4/4] 启动网站")
    print(f"  → http://{url_host}:{port}")
    if host == "0.0.0.0":
        print(f"  → 外网: http://<服务器公网IP>:{port}")
    print("  按 Ctrl+C 停止\n")

    os.chdir(BACKEND_DIR)
    subprocess.run(cmd, check=True)


def check_python_version() -> None:
    if sys.version_info >= (3, 7):
        return
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"错误: 当前 Python {ver} 过旧，本项目需要 Python 3.7 及以上。")
    sys.exit(1)


def main() -> None:
    if not BACKEND_DIR.exists():
        raise FileNotFoundError(f"Backend not found: {BACKEND_DIR}")

    check_python_version()
    print("=== 于洋洋 · 技术博客 一键启动 ===\n")
    py = ensure_venv()
    require_ssl(py)
    ensure_dependencies(py)
    ensure_video_assets(py)
    start_server(py)


if __name__ == "__main__":
    main()
