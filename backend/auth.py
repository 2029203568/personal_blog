"""管理后台登录：签名 Cookie 会话，保护浏览进度查询接口。"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated
from urllib.parse import unquote

from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

BASE_DIR = Path(__file__).resolve().parent
SECRET_FILE = BASE_DIR / "logs" / ".admin_secret"
COOKIE_NAME = "er_admin_session"
DEFAULT_NEXT = "/progress-dashboard"
SESSION_HOURS = int(os.getenv("ADMIN_SESSION_HOURS", "168"))


def _secret_bytes() -> bytes:
    env_key = os.getenv("ADMIN_SECRET", "").strip()
    if env_key:
        return env_key.encode("utf-8")
    if SECRET_FILE.is_file():
        return SECRET_FILE.read_text(encoding="utf-8").strip().encode("utf-8")
    key = secrets.token_hex(32)
    SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    SECRET_FILE.write_text(key, encoding="utf-8")
    return key.encode("utf-8")


DEFAULT_ADMIN_USERNAME = "15204959246"
DEFAULT_ADMIN_PASSWORD = "yuyang907017"


def admin_credentials() -> tuple[str, str]:
    return (
        os.getenv("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME).strip(),
        os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD),
    )


def verify_login(username: str, password: str) -> bool:
    expected_user, expected_pass = admin_credentials()
    return secrets.compare_digest(username.strip(), expected_user) and secrets.compare_digest(
        password, expected_pass
    )


def create_session(username: str) -> str:
    payload = {
        "u": username,
        "exp": int(time.time()) + SESSION_HOURS * 3600,
        "n": secrets.token_hex(8),
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    sig = hmac.new(_secret_bytes(), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def verify_session(token: str | None) -> str | None:
    if not token or "." not in token:
        return None
    raw, sig = token.rsplit(".", 1)
    expected = hmac.new(_secret_bytes(), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    if not secrets.compare_digest(expected, sig):
        return None
    padded = raw + "=" * (-len(raw) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")))
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return None
    if int(payload.get("exp", 0)) < time.time():
        return None
    user = payload.get("u")
    return user if isinstance(user, str) and user else None


def get_session_user(request: Request) -> str | None:
    return verify_session(request.cookies.get(COOKIE_NAME))


def safe_next_url(raw: str | None) -> str:
    if not raw:
        return DEFAULT_NEXT
    path = unquote(raw.strip())
    if not path.startswith("/") or path.startswith("//") or "://" in path:
        return DEFAULT_NEXT
    return path


def login_redirect(next_url: str | None = None) -> RedirectResponse:
    target = safe_next_url(next_url)
    return RedirectResponse(url=f"/admin/login?next={target}", status_code=302)


def require_admin(request: Request) -> str:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")
    return user


AdminUser = Annotated[str, Depends(require_admin)]


def require_admin_page(request: Request) -> str | RedirectResponse:
    user = get_session_user(request)
    if not user:
        return login_redirect(request.url.path)
    return user
