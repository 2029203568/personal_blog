"""每次启动写入演示视频 / 交付脚本的同步记录（Markdown）。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from code_assets import CODE_CATALOG, CODE_DIR, catalog_output_path as code_output_path
from code_assets import find_source_file as find_code_source
from video_assets import SOURCE_DIRS as VIDEO_SOURCE_DIRS
from video_assets import VIDEO_CATALOG, VIDEOS_DIR, catalog_output_path, find_source_file

SYNC_REPORT = VIDEOS_DIR / "资源同步记录.md"


def _fmt_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _row_status(output: Path, source: Path | None) -> tuple[str, str]:
    if output.is_file():
        return "✅ 已就绪", _fmt_size(output.stat().st_size)
    if source:
        return "⚠️ 待同步（源文件存在但未复制）", _fmt_size(source.stat().st_size)
    return "❌ 缺失", "—"


def _source_hint(sources: list[str]) -> str:
    return " / ".join(sources)


def _dirs_text(dirs: list[Path]) -> str:
    return "\n".join(f"- `{d}`" for d in dirs)


def build_sync_report() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    video_rows: list[str] = []
    code_rows: list[str] = []
    missing_videos: list[str] = []
    missing_codes: list[str] = []

    for entry in VIDEO_CATALOG:
        output = catalog_output_path(entry)
        source = find_source_file(entry["sources"])
        status, size = _row_status(output, source)
        if not output.is_file():
            missing_videos.append(entry["output"])
        source_path = str(source) if source else "未找到"
        video_rows.append(
            f"| `{entry['output']}` | {_source_hint(entry['sources'])} | {status} | {size} | "
            f"`/assets/videos/{entry['output']}` | `{source_path}` |"
        )

    for entry in CODE_CATALOG:
        output = code_output_path(entry)
        source = find_code_source(entry["sources"])
        status, size = _row_status(output, source)
        if not output.is_file():
            missing_codes.append(entry["output"])
        source_path = str(source) if source else "未找到"
        code_rows.append(
            f"| `{entry['output']}` | {_source_hint(entry['sources'])} | {status} | {size} | "
            f"`/assets/code/{entry['output']}` | `{source_path}` |"
        )

    all_ok = not missing_videos and not missing_codes
    summary = "全部就绪" if all_ok else "存在缺失项，请按下方说明补齐后重新运行 `python start_site.py`"

    lines = [
        "# 演示资源同步记录",
        "",
        "> **本文件由 `start_site.py` 每次启动时自动更新，请勿手改。**",
        "> 新增视频或脚本时：先在 `backend/video_assets.py` / `backend/code_assets.py` 登记，",
        "> 再把源文件放入下方「源目录」，最后重新启动网站。",
        "",
        f"**最近检查时间**：{now}  ",
        f"**同步结论**：{summary}",
        "",
        "## 演示视频",
        "",
        "| 站点文件 | 期望源文件名 | 状态 | 大小 | 访问路径 | 实际源路径 |",
        "| --- | --- | --- | --- | --- | --- |",
        *video_rows,
        "",
        "## 交付脚本",
        "",
        "| 站点文件 | 期望源文件名 | 状态 | 大小 | 访问路径 | 实际源路径 |",
        "| --- | --- | --- | --- | --- | --- |",
        *code_rows,
        "",
        "## 源目录（按优先级检索）",
        "",
        "**演示视频**",
        "",
        _dirs_text(VIDEO_SOURCE_DIRS),
        "",
        f"**站点目录**：`{VIDEOS_DIR}`",
        "",
        "**交付脚本**（检索项目上级目录及项目根目录）",
        "",
        f"- `{CODE_DIR}`",
        "",
        "## 新增资源 Checklist",
        "",
        "1. 将 MP4 放入 `产品示例视频/`，或将 `.py` 放入项目上级目录（与 `elphant-route` 同级）",
        "2. 在 `backend/video_assets.py` 的 `VIDEO_CATALOG` 或 `backend/code_assets.py` 的 `CODE_CATALOG` 增加条目",
        "3. 运行 `python start_site.py` 或 `python scripts/sync_videos.py`",
        "4. 打开本文件确认对应行状态为 **✅ 已就绪**",
        "",
        "## 仅手动同步（不启动网站）",
        "",
        "```bash",
        "python scripts/sync_videos.py",
        "python scripts/sync_code.py",
        "```",
        "",
    ]

    if missing_videos:
        lines.extend([
            "## ⚠️ 当前缺失的演示视频",
            "",
            *(f"- `{name}`" for name in missing_videos),
            "",
        ])

    if missing_codes:
        lines.extend([
            "## ⚠️ 当前缺失的交付脚本",
            "",
            *(f"- `{name}`" for name in missing_codes),
            "",
        ])

    return "\n".join(lines)


def write_sync_report() -> Path:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    SYNC_REPORT.write_text(build_sync_report(), encoding="utf-8")
    return SYNC_REPORT
