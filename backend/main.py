from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any, Dict, List

# HLS 静态资源 MIME（部分 Linux 默认未注册）
mimetypes.add_type("application/vnd.apple.mpegurl", ".m3u8")
mimetypes.add_type("application/x-mpegURL", ".m3u8")
mimetypes.add_type("video/mp2t", ".ts")
mimetypes.add_type("video/MP2T", ".ts")

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from auth import (
    COOKIE_NAME,
    AdminUser,
    SESSION_HOURS,
    create_session,
    get_session_user,
    login_redirect,
    require_admin_page,
    safe_next_url,
    verify_login,
)

from data import (
    CASE_SECTIONS,
    CASES,
    CONTACT,
    DEMO_VIDEOS,
    DOMAINS,
    HERO,
    PROCESS,
    PROJECTS,
    PROJECTS_SECTION,
    SIDE_NAV,
    SITE,
    SKILLS,
    STATS,
)
from media_serve import register_video_routes
from progress_logger import compute_stats, read_progress, upsert_progress
from visit_logger import VisitLogMiddleware, read_visits


def pydantic_dict(model: BaseModel) -> dict:
    dump = getattr(model, "model_dump", None)
    if callable(dump):
        return dump()
    return model.dict()


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
CASES_DIR = FRONTEND_DIR / "assets" / "cases"
VIDEOS_DIR = FRONTEND_DIR / "assets" / "videos"


def _resolve_demo_videos() -> list:
    """若已跑过 transcode，优先返回 HLS；否则仅 MP4。"""
    resolved = []
    for item in DEMO_VIDEOS:
        entry = dict(item)
        hls_url = entry.get("video_hls", "")
        if hls_url:
            rel_path = hls_url[len("/assets/") :] if hls_url.startswith("/assets/") else hls_url.lstrip("/")
            hls_file = FRONTEND_DIR / "assets" / rel_path
            if not hls_file.is_file():
                entry.pop("video_hls", None)
        resolved.append(entry)
    return resolved

app = FastAPI(
    title="于洋洋 · 技术博客 API",
    description="Personal tech blog landing page backend",
    version="1.0.0",
)

app.add_middleware(VisitLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ContactRequest(BaseModel):
    email: EmailStr
    message: str = Field(min_length=1, max_length=2000)


class ContactResponse(BaseModel):
    success: bool
    message: str


class ProgressPayload(BaseModel):
    session_id: str = Field(min_length=1)
    page: str = Field(min_length=1)
    path: str = Field(min_length=1)
    started_at: str = ""
    ended_at: str = ""
    max_scroll_pct: int = Field(default=0, ge=0, le=100)
    sections_viewed: List[str] = Field(default_factory=list)
    deepest_section: str = ""
    section_order: List[str] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    duration_sec: int = Field(default=0, ge=0)


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


SCREENSHOT_CATEGORY = {
    "category_id": "delivery-screenshots",
    "category_name": "项目交付截图",
}


def _build_case_sections(items: list[dict]) -> list[dict]:
    demo_videos = _resolve_demo_videos()
    sections = []
    for section in CASE_SECTIONS:
        if section["type"] == "videos" and demo_videos:
            sections.append({**section, "items": demo_videos})
        elif section["type"] == "screenshots" and items:
            sections.append({**section, "items": items})
    return sections


@app.get("/api/landing")
def get_landing():
    return {
        "site": SITE,
        "hero": HERO,
        "stats": STATS,
        "skills": SKILLS,
        "domains": DOMAINS,
        "projects": PROJECTS,
        "projects_section": PROJECTS_SECTION,
        "process": PROCESS,
        "contact": CONTACT,
        "side_nav": SIDE_NAV,
    }


@app.post("/api/contact", response_model=ContactResponse)
def contact(body: ContactRequest):
    return ContactResponse(
        success=True,
        message=f"感谢留言！我会尽快回复 {body.email}",
    )


@app.get("/api/visits")
def get_visits(_user: AdminUser):
    """查看访问记录（需登录）。"""
    records = read_visits()
    return {
        "total": len(records),
        "file": "backend/logs/visits.json",
        "records": records[-100:],
    }


@app.post("/api/admin/login")
def admin_login(body: AdminLoginRequest, response: Response, next: str = "/progress-dashboard"):
    if not verify_login(body.username, body.password):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = create_session(body.username.strip())
    redirect_to = safe_next_url(next)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_HOURS * 3600,
        path="/",
    )
    return {"success": True, "redirect": redirect_to}


@app.post("/api/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"success": True}


@app.get("/api/admin/me")
def admin_me(request: Request):
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    return {"authenticated": True, "username": user}


@app.post("/api/progress")
def post_progress(body: ProgressPayload, request: Request):
    """合并写入浏览进度（前端 pagehide / sendBeacon 上报）。"""
    try:
        record = upsert_progress(pydantic_dict(body), request)
        return {"success": True, "record": record}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/progress")
def get_progress(limit: int = 100, _user: AdminUser = ...):
    """查看浏览进度记录（需登录）。"""
    records = read_progress(limit=min(limit, 500))
    return {
        "total": len(records),
        "file": "backend/logs/progress.json",
        "records": records,
    }


@app.get("/api/progress/stats")
def get_progress_stats(_user: AdminUser):
    """浏览进度汇总统计（需登录）。"""
    return compute_stats()


@app.get("/api/cases")
def get_cases():
    items = []
    if CASES_DIR.exists():
        files = sorted(
            (f for f in CASES_DIR.iterdir() if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}),
            key=lambda p: int(p.stem) if p.stem.isdigit() else p.name.lower(),
        )
        for index, file in enumerate(files, start=1):
            items.append({
                "id": index,
                "title": f"交付截图 {index}",
                "image": f"/assets/cases/{file.name}",
                **SCREENSHOT_CATEGORY,
            })
    sections = _build_case_sections(items)
    return {
        "site": SITE,
        "cases": CASES,
        "contact": CONTACT,
        "items": items,
        "sections": sections,
        "demo_videos": _resolve_demo_videos(),
        "video_count": len(DEMO_VIDEOS),
        "total": len(items),
    }


@app.get("/admin/login")
def serve_admin_login():
    page = FRONTEND_DIR / "admin-login.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="Login page not found")
    return FileResponse(page)


@app.get("/progress-dashboard")
def serve_progress_dashboard(request: Request):
    auth = require_admin_page(request)
    if isinstance(auth, RedirectResponse):
        return auth
    page = FRONTEND_DIR / "progress-dashboard.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="Progress dashboard not found")
    return FileResponse(page)


@app.get("/cases")
def serve_cases():
    page = FRONTEND_DIR / "cases.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="Cases page not found")
    return FileResponse(page)


@app.get("/")
def serve_index():
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index)


# 兼容旧版或 Nginx 静态目录中的路径写法
@app.get("/style.css", include_in_schema=False)
def legacy_style_css():
    return RedirectResponse(url="/css/style.css", status_code=307)


@app.get("/main.js", include_in_schema=False)
def legacy_main_js():
    return RedirectResponse(url="/js/main.js", status_code=307)


@app.get("/progress-tracker.js", include_in_schema=False)
def legacy_progress_tracker_js():
    return RedirectResponse(url="/js/progress-tracker.js", status_code=307)


@app.get("/cases.js", include_in_schema=False)
def legacy_cases_js():
    return RedirectResponse(url="/js/cases.js", status_code=307)


# 视频走 Range 专用路由（须在 /assets 静态挂载之前注册）
register_video_routes(app, VIDEOS_DIR)

app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
