#!/usr/bin/env python3
"""
将 elphant-route 项目推送到 GitHub。

默认仓库: https://github.com/2029203568/-

用法:
  python scripts/push_to_github.py
  python scripts/push_to_github.py --message "更新演示视频与登录后台"
  python scripts/push_to_github.py --dry-run
  python scripts/push_to_github.py --remote https://github.com/USER/REPO.git

认证（任选其一）:
  1. 已配置 git credential / SSH
  2. 环境变量 GITHUB_TOKEN（Personal Access Token，需 repo 权限）
     Windows PowerShell:
       $env:GITHUB_TOKEN="ghp_xxxx"
       python scripts/push_to_github.py
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REMOTE = "https://github.com/2029203568/-.git"
DEFAULT_BRANCH = "main"

# 推送前若仍被跟踪则中止，避免泄露
BLOCKED_TRACKED = (
    "backend/logs/.admin_secret",
    "backend/logs/visits.json",
    "backend/logs/progress.json",
    "natapp/config.ini",
    ".env",
)


def run(cmd: list[str], *, cwd: Path = PROJECT_ROOT, check: bool = True, echo: str | None = None) -> subprocess.CompletedProcess:
    print("+", echo if echo is not None else " ".join(cmd))
    return subprocess.run(cmd, cwd=str(cwd), check=check, text=True)


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(PROJECT_ROOT),
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def ensure_git_repo() -> None:
    if not (PROJECT_ROOT / ".git").is_dir():
        print(f"初始化 Git 仓库: {PROJECT_ROOT}")
        run(["git", "init", "-b", DEFAULT_BRANCH])


def normalize_remote(url: str) -> str:
    u = url.strip().rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    return u.lower()


def ensure_remote(remote_url: str) -> None:
    remotes = git_output("remote")
    if "origin" not in remotes.splitlines():
        run(["git", "remote", "add", "origin", remote_url])
        return
    current = git_output("remote", "get-url", "origin")
    if normalize_remote(current) != normalize_remote(remote_url):
        print(f"更新 origin: {current} → {remote_url}")
        run(["git", "remote", "set-url", "origin", remote_url])


def check_blocked_files() -> None:
    tracked = git_output("ls-files").splitlines()
    blocked = [p for p in BLOCKED_TRACKED if p in tracked]
    if blocked:
        print("错误: 以下敏感文件已被 Git 跟踪，请先移除后再推送:")
        for path in blocked:
            print(f"  - {path}")
        print("\n可执行: git rm --cached <文件路径>")
        sys.exit(1)


def has_changes() -> bool:
    status = git_output("status", "--porcelain")
    return bool(status)


def git_push(remote_url: str, branch: str, token: str) -> None:
    """推送时禁用 Windows 凭据缓存，改用 Bearer Token（兼容 fine-grained PAT）。"""
    cmd = ["git", "-c", "credential.helper="]
    if token:
        cmd.extend(["-c", f"http.extraHeader=Authorization: Bearer {token}"])
    cmd.extend(["push", "-u", remote_url, f"HEAD:{branch}"])
    hint = " (GITHUB_TOKEN Bearer)" if token else ""
    run(cmd, echo=f"git push -u {remote_url} HEAD:{branch}{hint}")


def main() -> None:
    parser = argparse.ArgumentParser(description="推送 elphant-route 到 GitHub")
    parser.add_argument("--remote", default=os.environ.get("GITHUB_REMOTE", DEFAULT_REMOTE))
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--message", "-m", default="chore: sync elphant-route project")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要执行的 git 命令")
    parser.add_argument("--skip-push", action="store_true", help="只 commit，不 push")
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)
    print(f"项目目录: {PROJECT_ROOT}")
    print(f"目标仓库: {args.remote}")
    print(f"目标分支: {args.branch}\n")

    if args.dry_run:
        print("[dry-run] 将执行: git init / remote / add / commit / push")
        return

    ensure_git_repo()
    ensure_remote(args.remote)
    check_blocked_files()

    run(["git", "add", "-A"])
    if not has_changes():
        print("没有需要提交的变更，跳过 commit。")
    else:
        print("\n--- 即将提交的变更 ---")
        run(["git", "status", "-sb"], check=True)
        run(["git", "commit", "-m", args.message])

    if args.skip_push:
        print("\n已跳过 push（--skip-push）。")
        return

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("警告: 未设置 GITHUB_TOKEN，将使用系统已保存的 Git 凭据。")
    git_push(args.remote, args.branch, token)
    print(f"\n完成: {args.remote} (分支 {args.branch})")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"\nGit 命令失败 (exit {exc.returncode})。")
        if exc.returncode == 128 or "403" in str(exc):
            print(
                "403 常见原因:\n"
                "  1. Token 未勾选仓库 2029203568/- 的 Contents 读写权限\n"
                "  2. Windows 缓存了旧密码 — 打开「凭据管理器」删除 git:https://github.com\n"
                "  3. Token 已过期或被撤销 — 重新生成后: $env:GITHUB_TOKEN=\"新token\""
            )
        elif not os.environ.get("GITHUB_TOKEN"):
            print(
                "提示: 请设置 Personal Access Token:\n"
                "  PowerShell: $env:GITHUB_TOKEN=\"ghp_或_github_pat_...\"\n"
                "  然后重新运行本脚本。"
            )
        sys.exit(exc.returncode)
