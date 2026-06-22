"""视频 / HLS 静态资源：显式支持 HTTP Range（206），便于拖拽进度与边下边播。"""
from __future__ import annotations

import mimetypes
import os
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

VIDEO_MEDIA_TYPES = {
    ".mp4": "video/mp4",
    ".m3u8": "application/vnd.apple.mpegurl",
    ".ts": "video/mp2t",
}

STREAMING_HEADERS = {
    "Accept-Ranges": "bytes",
    "Cache-Control": "public, max-age=86400",
}


def _safe_path(base: Path, rel: str) -> Path:
    target = (base / rel).resolve()
    base_resolved = base.resolve()
    if not str(target).startswith(str(base_resolved)):
        raise HTTPException(status_code=404, detail="Not found")
    return target


def _media_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_MEDIA_TYPES:
        return VIDEO_MEDIA_TYPES[ext]
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def range_file_response(request: Request, path: Path) -> FileResponse:
    """FileResponse 在 Starlette 内会根据 Range 头返回 206 Partial Content。"""
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(
        path=str(path),
        media_type=_media_type(path),
        stat_result=os.stat(path),
        headers=dict(STREAMING_HEADERS),
    )


def register_video_routes(app, videos_dir: Path) -> None:
    """须在 app.mount('/assets', ...) 之前注册。"""

    @app.api_route(
        "/assets/videos/{file_path:path}",
        methods=["GET", "HEAD"],
        name="serve_video_asset",
    )
    async def serve_video_asset(request: Request, file_path: str):
        target = _safe_path(videos_dir, file_path)
        return range_file_response(request, target)
