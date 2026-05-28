from __future__ import annotations

from datetime import datetime, timezone
import sqlite3
from typing import Any

from app.config import settings

ALLOWED_SCORES = {"high", "medium", "low"}
ALLOWED_STATUSES = {
    "new",
    "to_write",
    "written",
    "replied",
    "demo",
    "trial",
    "rejected",
    "client",
}

LEAD_FIELDS = (
    "id",
    "company",
    "city",
    "niche",
    "source",
    "contacts",
    "website",
    "telegram",
    "vk",
    "fit_reason",
    "score",
    "status",
    "notes",
    "created_at",
    "updated_at",
)

SEARCH_FIELDS = (
    "company",
    "city",
    "niche",
    "source",
    "contacts",
    "website",
    "telegram",
    "vk",
    "fit_reason",
    "notes",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {field: row[field] for field in LEAD_FIELDS}


def _validate_score(score: str) -> None:
    if score not in ALLOWED_SCORES:
        raise ValueError(f"Invalid score: {score}")


def _validate_status(status: str) -> None:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status: {status}")


def create_lead(
    *,
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
    company = company.strip()
    if not company:
        raise ValueError("Company is required")

    _validate_score(score)
    _validate_status(status)

    now = _utc_now_iso()
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO leads (
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
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company,
                city.strip(),
                niche.strip(),
                source.strip(),
                contacts.strip(),
                website.strip(),
                telegram.strip(),
                vk.strip(),
                fit_reason.strip(),
                score,
                status,
                notes.strip(),
                now,
                now,
            ),
        )
        connection.commit()
        lead_id = cursor.lastrowid

    lead = get_lead(int(lead_id))
    if lead is None:
        raise RuntimeError("Lead was not created")
    return lead


def get_lead(lead_id: int) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT id, company, city, niche, source, contacts, website, telegram, vk,
                   fit_reason, score, status, notes, created_at, updated_at
            FROM leads
            WHERE id = ?
            """,
            (lead_id,),
        ).fetchone()
    return _row_to_dict(row)


def list_recent_leads(limit: int = 10) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), 50))
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, company, city, niche, source, contacts, website, telegram, vk,
                   fit_reason, score, status, notes, created_at, updated_at
            FROM leads
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def search_leads(query: str, limit: int = 10) -> list[dict[str, Any]]:
    query = query.strip()
    if not query:
        return []

    safe_limit = max(1, min(int(limit), 50))
    like_query = f"%{query}%"
    where_clause = " OR ".join(f"{field} LIKE ?" for field in SEARCH_FIELDS)
    params = [like_query for _ in SEARCH_FIELDS]

    with _connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, company, city, niche, source, contacts, website, telegram, vk,
                   fit_reason, score, status, notes, created_at, updated_at
            FROM leads
            WHERE {where_clause}
            ORDER BY id DESC
            LIMIT ?
            """,
            (*params, safe_limit),
        ).fetchall()
    return [dict(row) for row in rows]


def update_lead_status(lead_id: int, status: str) -> dict[str, Any] | None:
    _validate_status(status)
    now = _utc_now_iso()
    with _connect() as connection:
        cursor = connection.execute(
            """
            UPDATE leads
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, now, lead_id),
        )
        connection.commit()
        if cursor.rowcount == 0:
            return None
    return get_lead(lead_id)


def update_lead_score(lead_id: int, score: str) -> dict[str, Any] | None:
    _validate_score(score)
    now = _utc_now_iso()
    with _connect() as connection:
        cursor = connection.execute(
            """
            UPDATE leads
            SET score = ?, updated_at = ?
            WHERE id = ?
            """,
            (score, now, lead_id),
        )
        connection.commit()
        if cursor.rowcount == 0:
            return None
    return get_lead(lead_id)
