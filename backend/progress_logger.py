"""浏览进度记录：按 session + 页面路径合并写入 JSON。"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from starlette.requests import Request

BASE_DIR = Path(__file__).resolve().parent
PROGRESS_FILE = BASE_DIR / "logs" / "progress.json"
CN_TZ = timezone(timedelta(hours=8))

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


def _now_iso() -> str:
    return datetime.now(CN_TZ).isoformat()


def _read_records() -> list[dict[str, Any]]:
    if not PROGRESS_FILE.exists():
        return []
    try:
        data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_records(records: list[dict[str, Any]]) -> None:
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    merged: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        key = (
            event.get("type"),
            event.get("section"),
            event.get("video_id"),
            event.get("pct"),
            event.get("index"),
            event.get("hash"),
            event.get("target"),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(event)
    return merged


def _merge_session_record(
    existing: dict[str, Any] | None,
    payload: dict[str, Any],
    request: Request,
) -> dict[str, Any]:
    now = _now_iso()
    if existing is None:
        record = {
            "session_id": payload.get("session_id", ""),
            "page": payload.get("page", ""),
            "path": payload.get("path", ""),
            "started_at": payload.get("started_at") or now,
            "ended_at": payload.get("ended_at") or now,
            "ip": _client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "max_scroll_pct": int(payload.get("max_scroll_pct") or 0),
            "sections_viewed": list(payload.get("sections_viewed") or []),
            "deepest_section": payload.get("deepest_section") or "",
            "events": list(payload.get("events") or []),
            "duration_sec": int(payload.get("duration_sec") or 0),
        }
    else:
        old_sections = set(existing.get("sections_viewed") or [])
        new_sections = set(payload.get("sections_viewed") or [])
        merged_sections = sorted(old_sections | new_sections)

        old_max = int(existing.get("max_scroll_pct") or 0)
        new_max = int(payload.get("max_scroll_pct") or 0)

        all_events = _dedupe_events(
            list(existing.get("events") or []) + list(payload.get("events") or [])
        )

        record = {
            **existing,
            "ended_at": payload.get("ended_at") or now,
            "max_scroll_pct": max(old_max, new_max),
            "sections_viewed": merged_sections,
            "deepest_section": payload.get("deepest_section") or existing.get("deepest_section", ""),
            "events": all_events,
            "duration_sec": max(
                int(existing.get("duration_sec") or 0),
                int(payload.get("duration_sec") or 0),
            ),
        }

    section_order = payload.get("section_order") or []
    if section_order and record.get("sections_viewed"):
        order_map = {sid: i for i, sid in enumerate(section_order)}
        viewed = record["sections_viewed"]
        deepest = max(viewed, key=lambda s: order_map.get(s, -1))
        record["deepest_section"] = deepest

    record["events"] = _dedupe_events(record.get("events") or [])
    return record


def upsert_progress(payload: dict[str, Any], request: Request) -> dict[str, Any]:
    session_id = str(payload.get("session_id") or "").strip()
    path = str(payload.get("path") or "").strip()
    if not session_id or not path:
        raise ValueError("session_id and path are required")

    with _file_lock:
        records = _read_records()
        idx = next(
            (
                i
                for i, r in enumerate(records)
                if r.get("session_id") == session_id and r.get("path") == path
            ),
            None,
        )
        existing = records[idx] if idx is not None else None
        merged = _merge_session_record(existing, payload, request)

        if idx is None:
            records.append(merged)
        else:
            records[idx] = merged

        _write_records(records)
        return merged


def read_progress(limit: int = 100) -> list[dict[str, Any]]:
    records = _read_records()
    return records[-limit:]


def compute_stats() -> dict[str, Any]:
    records = _read_records()
    if not records:
        return {
            "total_sessions": 0,
            "by_page": {},
            "avg_scroll_pct": 0,
            "section_counts": {},
            "top_sections": [],
            "video_milestones": {},
            "video_started_count": 0,
            "video_completed_count": 0,
            "video_completion_rate": 0,
            "event_counts": {},
        }

    by_page: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        page = rec.get("page") or rec.get("path") or "unknown"
        by_page.setdefault(page, []).append(rec)

    section_counts: dict[str, int] = {}
    event_counts: dict[str, int] = {}
    video_milestones: dict[str, dict[int, int]] = {}
    video_reached_100: set[str] = set()
    video_started: set[str] = set()

    scroll_sum = 0
    for rec in records:
        scroll_sum += int(rec.get("max_scroll_pct") or 0)
        for section in rec.get("sections_viewed") or []:
            section_counts[section] = section_counts.get(section, 0) + 1
        for event in rec.get("events") or []:
            if not isinstance(event, dict):
                continue
            etype = event.get("type") or "unknown"
            event_counts[etype] = event_counts.get(etype, 0) + 1
            if etype == "video_progress":
                vid = event.get("video_id") or "unknown"
                pct = int(event.get("pct") or 0)
                video_started.add(vid)
                if vid not in video_milestones:
                    video_milestones[vid] = {}
                video_milestones[vid][pct] = video_milestones[vid].get(pct, 0) + 1
                if pct >= 100:
                    video_reached_100.add(vid)

    page_stats = {}
    for page, items in by_page.items():
        if not items:
            continue
        page_stats[page] = {
            "sessions": len(items),
            "avg_scroll_pct": round(
                sum(int(r.get("max_scroll_pct") or 0) for r in items) / len(items),
                1,
            ),
        }

    completion_rate = 0.0
    if video_started:
        completion_rate = round(len(video_reached_100) / len(video_started) * 100, 1)

    top_sections = sorted(section_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_sessions": len(records),
        "by_page": page_stats,
        "avg_scroll_pct": round(scroll_sum / len(records), 1),
        "section_counts": dict(top_sections),
        "top_sections": [{"section": k, "count": v} for k, v in top_sections[:10]],
        "video_milestones": {
            vid: {str(p): c for p, c in sorted(m.items())}
            for vid, m in video_milestones.items()
        },
        "video_started_count": len(video_started),
        "video_completed_count": len(video_reached_100),
        "video_completion_rate": completion_rate,
        "event_counts": event_counts,
    }
