"""将网站访问记录追加写入 JSON 文件。"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

BASE_DIR = Path(__file__).resolve().parent
VISITS_FILE = BASE_DIR / "logs" / "visits.json"
CN_TZ = timezone(timedelta(hours=8))

# 记录页面访问与联系提交，不记录静态资源及重复 API 请求
LOGGED_PAGE_PATHS = frozenset({"/", "/cases"})
LOGGED_POST_PATHS = frozenset({"/api/contact"})

_file_lock = threading.Lock()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


def _page_label(path: str) -> str:
    labels = {
        "/": "首页",
        "/cases": "真实案例",
        "/api/contact": "联系提交",
    }
    return labels.get(path, path)


def _should_log(method: str, path: str) -> bool:
    if method == "GET" and path in LOGGED_PAGE_PATHS:
        return True
    if method == "POST" and path in LOGGED_POST_PATHS:
        return True
    return False


def build_visit_record(request: Request, method: str, path: str, status_code: int) -> dict[str, Any]:
    return {
        "time": datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": datetime.now(CN_TZ).isoformat(),
        "ip": _client_ip(request),
        "method": method,
        "path": path,
        "page": _page_label(path),
        "status": status_code,
        "user_agent": request.headers.get("user-agent", ""),
        "referer": request.headers.get("referer") or "",
        "host": request.headers.get("host", ""),
    }


def append_visit(record: dict[str, Any]) -> None:
    VISITS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _file_lock:
        records: list[dict[str, Any]] = []
        if VISITS_FILE.exists():
            try:
                raw = VISITS_FILE.read_text(encoding="utf-8").strip()
                if raw:
                    data = json.loads(raw)
                    if isinstance(data, list):
                        records = data
            except (json.JSONDecodeError, OSError):
                records = []

        records.append(record)
        VISITS_FILE.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def read_visits() -> list[dict[str, Any]]:
    if not VISITS_FILE.exists():
        return []
    try:
        data = json.loads(VISITS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


class VisitLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method.upper()
        path = request.url.path

        response = await call_next(request)

        if _should_log(method, path):
            try:
                record = build_visit_record(request, method, path, response.status_code)
                append_visit(record)
            except OSError:
                pass

        return response
