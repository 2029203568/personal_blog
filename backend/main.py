from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from data import CONTACT, DOMAINS, HERO, PROJECTS, SIDE_NAV, SITE, SKILLS, STATS

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app = FastAPI(
    title="于洋洋 · 技术博客 API",
    description="Personal tech blog landing page backend",
    version="1.0.0",
)

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


@app.get("/api/landing")
def get_landing():
    return {
        "site": SITE,
        "hero": HERO,
        "stats": STATS,
        "skills": SKILLS,
        "domains": DOMAINS,
        "projects": PROJECTS,
        "contact": CONTACT,
        "side_nav": SIDE_NAV,
    }


@app.post("/api/contact", response_model=ContactResponse)
def contact(body: ContactRequest):
    return ContactResponse(
        success=True,
        message=f"感谢留言！我会尽快回复 {body.email}",
    )


@app.get("/")
def serve_index():
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index)


app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
