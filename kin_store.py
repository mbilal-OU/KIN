"""Local SQLite persistence for KIN (plan Module T).

Scope and honesty notes:
  * This is a LOCAL single-user store for a guest profile on one machine.
  * It is NOT multi-user isolation, NOT encryption, and NOT an auth system.
    A hosted multi-user deployment would need real identities before this
    file could be reused as-is.
  * Only stdlib `sqlite3` is used, so no new dependency is introduced.

A new connection is opened per call because Streamlit executes scripts on
worker threads and SQLite connections are not thread-shareable by default.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from kin_models import MICHIGAN, DEFAULT_PREFERENCES, make_workspace

DB_PATH = Path(os.getenv("KIN_DB_PATH", Path(__file__).parent / "kin_local.db"))

_SCHEMA = """
-- assistant_alias is intentionally nullable:
--   NULL -> inherit the default assistant name from preferences
--   ''   -> the user explicitly chose to have no assistant name
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'Personal',
    assistant_alias TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commitments (
    id TEXT PRIMARY KEY,
    workspace_id TEXT,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_commitments_ws ON commitments(workspace_id);
CREATE TABLE IF NOT EXISTS actions (
    id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


#: Database paths whose schema has already been created in this process.
#: Schema creation must never depend on a UI-layer cache, so every connection
#: checks this first and the DDL is applied lazily exactly once per path.
_schema_ready: set[str] = set()


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    path = str(DB_PATH)
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        if path not in _schema_ready:
            connection.executescript(_SCHEMA)
            connection.commit()
            _schema_ready.add(path)
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    """Explicitly create the schema. Safe to call repeatedly."""
    _schema_ready.discard(str(DB_PATH))
    with _conn():
        pass


def _now() -> str:
    return datetime.now(MICHIGAN).isoformat()


# ---------------------------------------------------------------- preferences
def get_preferences() -> dict[str, Any]:
    prefs = dict(DEFAULT_PREFERENCES)
    with _conn() as c:
        for row in c.execute("SELECT key, value FROM preferences"):
            try:
                prefs[row["key"]] = json.loads(row["value"])
            except json.JSONDecodeError:
                continue
    return prefs


def set_preference(key: str, value: Any) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO preferences(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json.dumps(value)),
        )


def set_preferences(values: dict[str, Any]) -> None:
    for key, value in values.items():
        set_preference(key, value)


def reset_preferences() -> None:
    with _conn() as c:
        c.execute("DELETE FROM preferences")


# ----------------------------------------------------------------- workspaces
def list_workspaces() -> list[dict[str, Any]]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM workspaces ORDER BY created_at").fetchall()
    return [dict(r) for r in rows]


def add_workspace(workspace: dict[str, Any]) -> dict[str, Any]:
    with _conn() as c:
        c.execute(
            "INSERT INTO workspaces(id, name, kind, assistant_alias, created_at) VALUES(?,?,?,?,?)",
            (workspace["id"], workspace["name"], workspace["kind"],
             workspace.get("assistant_alias"), _now()),
        )
    return workspace


def update_workspace(workspace_id: str, **fields: Any) -> None:
    allowed = {k: v for k, v in fields.items() if k in ("name", "kind", "assistant_alias")}
    if not allowed:
        return
    assignments = ", ".join(f"{k} = ?" for k in allowed)
    with _conn() as c:
        c.execute(f"UPDATE workspaces SET {assignments} WHERE id = ?",
                  (*allowed.values(), workspace_id))


def delete_workspace(workspace_id: str) -> None:
    """Deleting a workspace also removes the commitments scoped to it."""
    with _conn() as c:
        c.execute("DELETE FROM commitments WHERE workspace_id = ?", (workspace_id,))
        c.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))


def ensure_default_workspace() -> dict[str, Any]:
    existing = list_workspaces()
    if existing:
        return existing[0]
    # assistant_alias stays NULL so the workspace inherits the preference default
    # and the user can still clear it to mean "no name at all".
    return add_workspace(make_workspace("My Life", "Personal"))


# ---------------------------------------------------------------- commitments
def list_commitments(workspace_id: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT payload FROM commitments"
    params: tuple[Any, ...] = ()
    if workspace_id:
        query += " WHERE workspace_id = ?"
        params = (workspace_id,)
    with _conn() as c:
        rows = c.execute(query, params).fetchall()
    items = [json.loads(r["payload"]) for r in rows]
    return sorted(items, key=lambda e: e.get("start", ""))


def save_commitment(commitment: dict[str, Any]) -> dict[str, Any]:
    with _conn() as c:
        c.execute(
            "INSERT INTO commitments(id, workspace_id, payload, created_at) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload, "
            "workspace_id = excluded.workspace_id",
            (commitment["id"], commitment.get("workspace_id"), json.dumps(commitment), _now()),
        )
    return commitment


def delete_commitment(commitment_id: str) -> None:
    with _conn() as c:
        c.execute("DELETE FROM commitments WHERE id = ?", (commitment_id,))


def commitment_exists(commitment_id: str) -> bool:
    with _conn() as c:
        row = c.execute("SELECT 1 FROM commitments WHERE id = ?", (commitment_id,)).fetchone()
    return row is not None


def find_duplicate(title: str, start: str, workspace_id: str | None) -> dict[str, Any] | None:
    """Guard against double-click / rerun duplicate insertion (plan T15)."""
    for existing in list_commitments(workspace_id):
        if existing.get("start") == start and existing.get("title", "").strip() == title.strip():
            return existing
    return None


# -------------------------------------------------------------------- actions
def list_actions(limit: int = 100) -> list[dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT payload FROM actions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [json.loads(r["payload"]) for r in rows]


def save_action(action: dict[str, Any]) -> dict[str, Any]:
    with _conn() as c:
        c.execute(
            "INSERT INTO actions(id, payload, created_at) VALUES(?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload",
            (action["id"], json.dumps(action), action.get("requested_at") or _now()),
        )
    return action


# -------------------------------------------------------------- notifications
def list_notifications(limit: int = 50) -> list[dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT payload FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [json.loads(r["payload"]) for r in rows]


def save_notification(notification: dict[str, Any]) -> dict[str, Any]:
    with _conn() as c:
        c.execute(
            "INSERT INTO notifications(id, payload, created_at) VALUES(?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET payload = excluded.payload",
            (notification["id"], json.dumps(notification), notification.get("created_at") or _now()),
        )
    return notification


def notification_exists(kind: str, related_id: str | None) -> bool:
    """Deduplication hook required by plan Module O."""
    for existing in list_notifications(200):
        if existing.get("kind") == kind and existing.get("related_id") == related_id:
            return True
    return False


def dismiss_notification(notification_id: str) -> None:
    with _conn() as c:
        row = c.execute("SELECT payload FROM notifications WHERE id = ?",
                        (notification_id,)).fetchone()
        if row:
            payload = json.loads(row["payload"])
            payload["status"] = "dismissed"
            c.execute("UPDATE notifications SET payload = ? WHERE id = ?",
                      (json.dumps(payload), notification_id))


# ------------------------------------------------------- export / erase (P/L)
def export_all() -> dict[str, Any]:
    """Everything KIN has stored locally, for user inspection or download."""
    return {
        "exported_at": _now(),
        "note": "Local KIN data only. No university or third-party records are included.",
        "preferences": get_preferences(),
        "workspaces": list_workspaces(),
        "commitments": list_commitments(),
        "actions": list_actions(500),
        "notifications": list_notifications(500),
    }


def erase_all() -> None:
    """Hard delete of every locally stored record."""
    with _conn() as c:
        for table in ("commitments", "actions", "notifications", "preferences", "workspaces"):
            c.execute(f"DELETE FROM {table}")
