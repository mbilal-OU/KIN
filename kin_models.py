"""Shared data models, enums and factories for KIN.

Pure data definitions only: no I/O, no Streamlit, no network calls.
Every datetime that crosses a module boundary is an ISO 8601 string with an
explicit UTC offset. See docs/ARCHITECTURE.md.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

MICHIGAN = ZoneInfo("America/Detroit")

# --------------------------------------------------------------------------
# Event taxonomy (plan Module C: "Support different event types")
# --------------------------------------------------------------------------
# icon is a plain unicode glyph so the UI needs no icon dependency.
EVENT_TYPES: dict[str, dict[str, Any]] = {
    "class":      {"label": "Class",        "icon": "\U0001F393", "travel": True},
    "exam":       {"label": "Exam",         "icon": "\U0001F4DD", "travel": True},
    "quiz":       {"label": "Quiz",         "icon": "❓",     "travel": True},
    "assignment": {"label": "Assignment",   "icon": "\U0001F4C4", "travel": False},
    "lab":        {"label": "Lab",          "icon": "\U0001F9EA", "travel": True},
    "meeting":    {"label": "Meeting",      "icon": "\U0001F465", "travel": True},
    "study":      {"label": "Study session","icon": "\U0001F4DA", "travel": False},
    "work":       {"label": "Work shift",   "icon": "\U0001F4BC", "travel": True},
    "family":     {"label": "Family",       "icon": "\U0001F3E1", "travel": True},
    "recreation": {"label": "Recreation",   "icon": "⚽",     "travel": True},
    "gaming":     {"label": "Gaming",       "icon": "\U0001F3AE", "travel": False},
    "personal":   {"label": "Personal",     "icon": "\U0001F4CC", "travel": False},
}
DEFAULT_EVENT_TYPE = "personal"

# Commitment lifecycle (plan Module J). "verified_complete" is reserved for
# evidence-backed completion; KIN never sets it from a calendar time passing.
COMMITMENT_STATUSES = ("planned", "in_progress", "completed", "canceled", "uncertain")

# Action lifecycle (plan Module K).
ACTION_PROPOSED = "PROPOSED"
ACTION_APPROVED = "APPROVED"
ACTION_EXECUTING = "EXECUTING"
ACTION_VERIFIED = "VERIFIED"
ACTION_REJECTED = "REJECTED"
ACTION_FAILED = "FAILED"

# Workspace presets. Users may type any label; these are only suggestions.
WORKSPACE_PRESETS = (
    "Personal", "University", "Course", "Research",
    "Employment", "Family", "Sports", "Gaming",
)

# Source trust labels (plan §31 "Definition of done").
SOURCE_LIVE = "Live and verified"
SOURCE_LOCAL = "Local and functional"
SOURCE_SIMULATED = "Simulated for demonstration"
SOURCE_BLOCKED = "Blocked by authorization"


def new_id(prefix: str) -> str:
    """Stable, collision-resistant identifier."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def event_type_meta(event_type: str | None) -> dict[str, Any]:
    return EVENT_TYPES.get(event_type or "", EVENT_TYPES[DEFAULT_EVENT_TYPE])


def michigan_offset_for(local_naive: datetime) -> str:
    """The correct UTC offset string for a wall-clock time in Michigan.

    Used to catch a model that emits -05:00 for a date that is actually EDT.
    """
    aware = local_naive.replace(tzinfo=MICHIGAN)
    offset = aware.utcoffset() or timedelta(0)
    total = int(offset.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return f"{sign}{total // 3600:02d}:{(total % 3600) // 60:02d}"


def make_commitment(
    title: str,
    start: str,
    end: str,
    *,
    event_type: str = DEFAULT_EVENT_TYPE,
    requires_travel: bool | None = None,
    workspace_id: str | None = None,
    origin: str = "manual",
    source_url: str | None = None,
    commitment_id: str | None = None,
    status: str = "planned",
    end_is_estimated: bool = False,
    notes: str = "",
) -> dict[str, Any]:
    """Build a commitment record. Callers must have validated start/end first."""
    meta = event_type_meta(event_type)
    return {
        "id": commitment_id or new_id("cmt"),
        "title": title.strip(),
        "start": start,
        "end": end,
        "event_type": event_type if event_type in EVENT_TYPES else DEFAULT_EVENT_TYPE,
        "requires_travel": bool(meta["travel"] if requires_travel is None else requires_travel),
        "workspace_id": workspace_id,
        "origin": origin,
        "source_url": source_url,
        "status": status if status in COMMITMENT_STATUSES else "planned",
        "end_is_estimated": bool(end_is_estimated),
        "notes": notes,
        "visibility": "private",
    }


def make_workspace(name: str, kind: str = "Personal",
                   assistant_alias: str | None = None) -> dict[str, Any]:
    """Create a workspace record.

    assistant_alias follows a three-way convention used throughout KIN:
      None -> inherit the default assistant name from preferences
      ''   -> the user explicitly wants no assistant name here
      text -> that name
    """
    return {
        "id": new_id("ws"),
        "name": name.strip() or "My Life",
        "kind": kind,
        "assistant_alias": assistant_alias if assistant_alias is None
                           else assistant_alias.strip(),
    }


def make_notification(
    kind: str,
    title: str,
    body: str,
    *,
    importance: str = "info",
    related_id: str | None = None,
    source: str = "KIN",
) -> dict[str, Any]:
    return {
        "id": new_id("ntf"),
        "kind": kind,
        "title": title,
        "body": body,
        "importance": importance,
        "related_id": related_id,
        "source": source,
        "created_at": datetime.now(MICHIGAN).isoformat(),
        "status": "unread",
    }


def make_action(action_type: str, summary: str, payload: dict[str, Any], rationale: str) -> dict[str, Any]:
    return {
        "id": new_id("act"),
        "type": action_type,
        "summary": summary,
        "payload": payload,
        "rationale": rationale,
        "status": ACTION_PROPOSED,
        "requested_at": datetime.now(MICHIGAN).isoformat(),
        "result": "",
        "verified": False,
    }


# Only preferences that something actually reads belong here. A stored value
# that no code consumes is a dead feature, so "interests" and "theme" were
# removed rather than left as decoration (light/dark is handled automatically
# by CSS via prefers-color-scheme).
DEFAULT_PREFERENCES: dict[str, Any] = {
    "preferred_name": "",          # greeting on Today
    "assistant_alias": "Navi",     # inherited default assistant name
    "commute_area": "Oakland University campus (approx.)",
    "planning_buffer": 45,         # travel buffer for alert overlap
    "opportunity_buffer": 30,      # buffer around a discovered event
    "transport_mode": "Car",       # shown as buffer context, sent to the model
    "favorite_teams": ["Oakland Golden Grizzlies"],  # filters Discover
    "quiet_hours_start": 22,       # collapses low-importance notices
    "quiet_hours_end": 7,
    "share_schedule_with_ai": True,
    "theme": "Auto",               # Auto | Light | Dark, applied by kin_theme.css
}
