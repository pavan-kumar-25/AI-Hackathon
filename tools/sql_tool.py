"""Read-only SQLite query tool with customer entitlement checks."""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from config import DB_PATH, MAX_SQL_ROWS

FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|"
    r"PRAGMA|VACUUM|REINDEX|TRIGGER|GRANT|REVOKE)\b",
    re.IGNORECASE,
)

SQL_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "query_db",
        "description": (
            "Run a read-only SELECT against ridewise.db. "
            "Use JOINs as needed. Limit result size. "
            "For customer sessions you MUST filter to that customer_id."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A single SELECT (or WITH ... SELECT) statement.",
                },
            },
            "required": ["sql"],
        },
    },
}


def _normalize_sql(sql: str) -> str:
    return sql.strip().rstrip(";").strip()


def _is_select_only(sql: str) -> bool:
    if FORBIDDEN.search(sql):
        return False
    # Allow WITH ... SELECT and plain SELECT only
    head = re.sub(r"\s+", " ", sql, flags=re.IGNORECASE).lstrip().upper()
    return head.startswith("SELECT") or head.startswith("WITH")


def _customer_entitled(sql: str, customer_id: str) -> tuple[bool, str]:
    """Require the session customer_id to appear when querying customer-owned data."""
    cid = customer_id.upper()
    sql_upper = sql.upper()
    mentions_cid = customer_id in sql or cid in sql_upper

    touches_owned = any(
        t in sql_upper
        for t in ("CUSTOMERS", "BOOKINGS", "PAYMENTS", "DAMAGE_REPORTS")
    )
    # Fleet-only queries (vehicles alone) are OK without customer_id
    if not touches_owned:
        return True, ""

    if not mentions_cid:
        return (
            False,
            f"Customer role requires filtering by customer_id = '{customer_id}'. "
            "Rewrite the SQL to include that filter (join bookings for payments/damage).",
        )
    return True, ""


def _post_filter_rows(
    columns: list[str],
    rows: list[tuple],
    role: str,
    customer_id: str | None,
) -> list[tuple]:
    if role != "customer" or not customer_id:
        return rows
    if "customer_id" not in columns:
        return rows
    idx = columns.index("customer_id")
    return [r for r in rows if str(r[idx]) == customer_id]


def query_db(
    sql: str,
    role: str = "agent",
    customer_id: str | None = None,
) -> dict[str, Any]:
    """Execute a read-only SQL query with entitlement enforcement."""
    sql = _normalize_sql(sql)
    if not sql:
        return {"ok": False, "error": "Empty SQL."}
    if not _is_select_only(sql):
        return {
            "ok": False,
            "error": "Only read-only SELECT/WITH queries are allowed.",
        }

    role = (role or "agent").lower()
    if role == "customer":
        if not customer_id:
            return {
                "ok": False,
                "error": "Customer role requires a customer_id before querying the database.",
            }
        ok, err = _customer_entitled(sql, customer_id)
        if not ok:
            return {"ok": False, "error": err}

    try:
        # URI read-only mode
        uri = f"file:{DB_PATH.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        try:
            cur = conn.execute(sql)
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(MAX_SQL_ROWS + 1)
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return {"ok": False, "error": f"SQL error: {exc}"}

    truncated = len(rows) > MAX_SQL_ROWS
    rows = rows[:MAX_SQL_ROWS]
    rows = _post_filter_rows(columns, rows, role, customer_id)

    return {
        "ok": True,
        "columns": columns,
        "rows": [list(r) for r in rows],
        "row_count": len(rows),
        "truncated": truncated,
    }
