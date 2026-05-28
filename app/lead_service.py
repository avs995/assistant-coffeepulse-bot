from __future__ import annotations

from datetime import datetime, timezone
import sqlite3
from typing import Any

from app.config import settings

ALLOWED_SCORES = {"high", "medium", "low"}
ALLOWED_STATUSES = {"new", "to_write", "written", "replied", "demo", "trial", "rejected", "client"}


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_lead(
    company: str,
    city: str = "",
    niche: str = "",
    source: str = "",
    contacts: str = "",
    website: str = "",
    telegram: str = "",
    vk: str = "",
    fit_reason: str = "",
    score: str = "medium",
    status: str = "new",
    notes: str = "",
) -> dict[str, Any]:
    if score not in ALLOWED_SCORES:
        raise ValueError("Invalid score")
    if status not in ALLOWED_STATUSES:
        raise ValueError("Invalid status")

    now = _now_iso()
    with _get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO leads (
                company, city, niche, source,
                contacts, website, telegram, vk,
                fit_reason, score, status, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company,
                city,
                niche,
                source,
                contacts,
                website,
                telegram,
                vk,
                fit_reason,
                score,
                status,
                notes,
                now,
                now,
            ),
        )
        lead_id = cur.lastrowid

    lead = get_lead(lead_id)
    if lead is None:
        raise RuntimeError("Lead creation failed")
    return lead


def get_lead(lead_id: int) -> dict[str, Any] | None:
    with _get_connection() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    return dict(row) if row else None


def list_recent_leads(limit: int = 10) -> list[dict[str, Any]]:
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def search_leads(query: str, limit: int = 10) -> list[dict[str, Any]]:
    like_query = f"%{query}%"
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM leads
            WHERE company LIKE ?
               OR city LIKE ?
               OR niche LIKE ?
               OR source LIKE ?
               OR contacts LIKE ?
               OR website LIKE ?
               OR telegram LIKE ?
               OR vk LIKE ?
               OR fit_reason LIKE ?
               OR notes LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (like_query,) * 10 + (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def update_lead_status(lead_id: int, status: str) -> dict[str, Any] | None:
    if status not in ALLOWED_STATUSES:
        raise ValueError("Invalid status")

    with _get_connection() as conn:
        cur = conn.execute(
            "UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
            (status, _now_iso(), lead_id),
        )
        if cur.rowcount == 0:
            return None

    return get_lead(lead_id)


def update_lead_score(lead_id: int, score: str) -> dict[str, Any] | None:
    if score not in ALLOWED_SCORES:
        raise ValueError("Invalid score")

    with _get_connection() as conn:
        cur = conn.execute(
            "UPDATE leads SET score = ?, updated_at = ? WHERE id = ?",
            (score, _now_iso(), lead_id),
        )
        if cur.rowcount == 0:
            return None

    return get_lead(lead_id)
