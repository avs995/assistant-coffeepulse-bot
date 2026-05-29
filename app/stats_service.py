from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3
from typing import Any

from app.config import settings

STATUSES = (
    "new",
    "to_write",
    "written",
    "replied",
    "demo",
    "trial",
    "rejected",
    "client",
)

CONTACTED_STATUSES = ("written", "replied", "demo", "trial", "rejected", "client")
REPLIED_STATUSES = ("replied", "demo", "trial", "client")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _period_start(scope: str) -> str | None:
    now = _utc_now()
    if scope == "week":
        return (now - timedelta(days=7)).isoformat()
    if scope == "month":
        return (now - timedelta(days=30)).isoformat()
    return None


def _where_clause(scope: str) -> tuple[str, tuple[str, ...]]:
    since = _period_start(scope)
    if since is None:
        return "", ()
    return "WHERE created_at >= ?", (since,)


def _percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(part / total * 100, 1)


def get_stats(scope: str = "all") -> dict[str, Any]:
    if scope not in {"all", "week", "month"}:
        raise ValueError("Invalid stats scope")

    where_clause, params = _where_clause(scope)
    with _connect() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) AS count FROM leads {where_clause}",
            params,
        ).fetchone()["count"]

        status_rows = connection.execute(
            f"""
            SELECT status, COUNT(*) AS count
            FROM leads
            {where_clause}
            GROUP BY status
            """,
            params,
        ).fetchall()

    status_counts = {status: 0 for status in STATUSES}
    for row in status_rows:
        status = row["status"]
        if status in status_counts:
            status_counts[status] = row["count"]

    contacted = sum(status_counts[status] for status in CONTACTED_STATUSES)
    replied = sum(status_counts[status] for status in REPLIED_STATUSES)
    clients = status_counts["client"]

    return {
        "scope": scope,
        "total": total,
        "status_counts": status_counts,
        "contacted": contacted,
        "replied": replied,
        "clients": clients,
        "reply_conversion": _percent(replied, contacted),
        "client_conversion": _percent(clients, total),
    }
