"""Free-first KIN time tools.

These helpers are deterministic and never trigger device alarms, background
jobs, email, SMS, voice services, or paid API requests. The UI checks them while
it is open; the user must not rely on them for safety-critical alerts.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Any

from kin_core import parse_dt
from kin_models import MICHIGAN, new_id


def _utc_now(now: datetime | None = None) -> datetime:
    value = now if now is not None else datetime.now(timezone.utc)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("A timezone-aware clock is required")
    return value.astimezone(timezone.utc)


def create_reminder(
    title: str, due_at: datetime, *, workspace_id: str, notes: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Create a local reminder record; persistence requires a separate user action."""
    title = (title or "").strip()
    if not 1 <= len(title) <= 100:
        raise ValueError("Reminder title must be 1–100 characters")
    if len(notes) > 500:
        raise ValueError("Reminder notes must be at most 500 characters")
    if not workspace_id:
        raise ValueError("A workspace is required")
    if due_at.tzinfo is None or due_at.utcoffset() is None:
        raise ValueError("Due time must specify a timezone")
    stamp = _utc_now(now)
    deadline = due_at.astimezone(timezone.utc)
    if deadline <= stamp:
        raise ValueError("Choose a future reminder time")
    if deadline > stamp + timedelta(days=365):
        raise ValueError("Choose a reminder within the next year")
    return {
        "id": new_id("rem"),
        "title": title,
        "notes": notes,
        "due_at": due_at.isoformat(),
        "workspace_id": workspace_id,
        "status": "pending",
        "created_at": stamp.isoformat(),
    }


def due_reminders(
    reminders: list[dict[str, Any]], now: datetime | None = None
) -> list[dict[str, Any]]:
    """Pending local reminders with due times at/before now.

    Does not deliver notifications. Invalid records are ignored rather than
    silently treated as due.
    """
    current = _utc_now(now)
    result = []
    for item in reminders:
        if item.get("status") != "pending":
            continue
        try:
            due = parse_dt(item["due_at"]).astimezone(timezone.utc)
        except (KeyError, TypeError, ValueError):
            continue
        if due <= current:
            result.append(item)
    return sorted(result, key=lambda item: parse_dt(item["due_at"]))


def start_focus_timer(minutes: int, *, now: datetime | None = None) -> dict[str, Any]:
    if isinstance(minutes, bool) or not isinstance(minutes, int) or not 1 <= minutes <= 180:
        raise ValueError("A focus session must last between 1 and 180 minutes")
    started = _utc_now(now)
    seconds = minutes * 60
    return {
        "status": "running",
        "duration_seconds": seconds,
        "remaining_seconds": seconds,
        "deadline": (started + timedelta(seconds=seconds)).isoformat(),
    }


def seconds_remaining(timer: dict[str, Any] | None,
                      *, now: datetime | None = None) -> int:
    if not timer:
        return 0
    if timer.get("status") == "paused":
        return max(0, int(timer.get("remaining_seconds", 0)))
    if timer.get("status") != "running":
        return 0
    deadline = parse_dt(timer["deadline"]).astimezone(timezone.utc)
    return max(0, ceil((deadline - _utc_now(now)).total_seconds()))


def pause_focus_timer(timer: dict[str, Any], *,
                      now: datetime | None = None) -> dict[str, Any]:
    if timer.get("status") != "running":
        raise ValueError("Only a running timer can be paused")
    remaining = seconds_remaining(timer, now=now)
    return {
        **timer,
        "status": "paused" if remaining else "finished",
        "remaining_seconds": remaining,
        "deadline": None,
    }


def resume_focus_timer(timer: dict[str, Any], *,
                       now: datetime | None = None) -> dict[str, Any]:
    if timer.get("status") != "paused":
        raise ValueError("Only a paused timer can be resumed")
    remaining = seconds_remaining(timer, now=now)
    if not remaining:
        raise ValueError("This focus session has already finished")
    return {
        **timer, "status": "running",
        "deadline": (_utc_now(now) + timedelta(seconds=remaining)).isoformat(),
    }
