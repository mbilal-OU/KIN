"""Free-first life-planning helpers for manually entered commitments.

All decisions are deterministic. No language model, network request, university
calendar access or external scheduling action is needed.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from kin_core import parse_dt
from kin_models import MICHIGAN, make_commitment, new_id

SCHEDULING_MODES = ("fixed", "flexible", "protected")
REPEAT_RULES = ("Once", "Every day", "Weekdays", "Every week")
FLEXIBLE_TYPES = frozenset(("personal", "recreation", "gaming", "study"))


def default_scheduling_mode(event_type: str) -> str:
    """Classes, exams, work and meetings default to fixed, not movable."""
    return "flexible" if event_type in FLEXIBLE_TYPES else "fixed"


def _wall_time(day: date, clock: time) -> datetime:
    """Resolve a Michigan wall-clock time without guessing at DST transitions.

    Ambiguous and non-existent times require the user to choose another time.
    This avoids silently shifting a recurring routine during a DST change.
    """
    naive = datetime.combine(day, clock.replace(tzinfo=None))
    aware = naive.replace(tzinfo=MICHIGAN)
    alternate = naive.replace(tzinfo=MICHIGAN, fold=1)
    roundtrip = aware.astimezone(timezone.utc).astimezone(MICHIGAN)
    if roundtrip.replace(tzinfo=None) != naive:
        raise ValueError("The selected local time does not exist during a daylight-saving change")
    if aware.utcoffset() != alternate.utcoffset():
        raise ValueError("The selected local time is ambiguous during a daylight-saving change")
    return aware


def build_manual_occurrences(
    title: str,
    first_day: date,
    start_time: time,
    end_time: time,
    *,
    event_type: str = "personal",
    requires_travel: bool = False,
    workspace_id: str | None = None,
    scheduling_mode: str = "fixed",
    repeat: str = "Once",
    weeks: int = 1,
    notes: str = "",
) -> list[dict[str, Any]]:
    """Build individual local records, not a live RRULE/calendar subscription.

    The caller previews/confirms the plan and persists the returned records.
    Repeated records share a series_id but can be edited or removed individually.
    Maximum 12 weeks / 84 occurrences prevents accidental bulk inserts.
    """
    if not 1 <= len(title.strip()) <= 100:
        raise ValueError("Enter a title of 1 to 100 characters")
    if scheduling_mode not in SCHEDULING_MODES:
        raise ValueError("Unknown scheduling mode")
    if repeat not in REPEAT_RULES:
        raise ValueError("Unknown repeat rule")
    if isinstance(weeks, bool) or not isinstance(weeks, int) or not 1 <= weeks <= 12:
        raise ValueError("Repeat duration must be between 1 and 12 weeks")
    if repeat == "Once":
        dates = [first_day]
    elif repeat == "Every week":
        dates = [first_day + timedelta(weeks=i) for i in range(weeks)]
    else:
        dates = [first_day + timedelta(days=i) for i in range(7 * weeks)
                 if repeat == "Every day"
                 or (first_day + timedelta(days=i)).weekday() < 5]

    group_id = new_id("series") if repeat != "Once" else None
    records = []
    for day in dates:
        start = _wall_time(day, start_time)
        end = _wall_time(day, end_time)
        elapsed = end.astimezone(timezone.utc) - start.astimezone(timezone.utc)
        if not timedelta(0) < elapsed <= timedelta(hours=24):
            raise ValueError("End time must follow start time on the same day")
        item = make_commitment(
            title, start.isoformat(), end.isoformat(),
            event_type=event_type, requires_travel=requires_travel,
            workspace_id=workspace_id, origin="manual", notes=notes,
        )
        item["scheduling_mode"] = scheduling_mode
        if group_id is not None:
            item["series_id"] = group_id
            item["repeat_rule"] = repeat
        records.append(item)
    return records


def suggest_alternative_slots(
    commitments: list[dict[str, Any]],
    target_id: str,
    *,
    days_ahead: int = 7,
    earliest_hour: int = 7,
    latest_hour: int = 22,
    step_minutes: int = 15,
    max_results: int = 5,
    buffer_minutes: int = 0,
    not_before: datetime | None = None,
) -> list[dict[str, Any]]:
    """Suggest empty slots for a FLEXIBLE commitment without mutating anything.

    Only commitments supplied by the caller are considered; callers must scope
    to a workspace and disclose that other calendars are not considered.
    An optional buffer is a user-chosen spacing preference, NOT travel ETA.
    Proposals are not permission to move a class, employer shift or appointment.
    """
    if not 1 <= days_ahead <= 14:
        raise ValueError("days_ahead must be between 1 and 14")
    if not 0 <= earliest_hour < latest_hour <= 23:
        raise ValueError("Invalid search hours")
    if step_minutes not in (5, 10, 15, 20, 30, 60):
        raise ValueError("Unsupported time step")
    if not 1 <= max_results <= 20 or not 0 <= buffer_minutes <= 120:
        raise ValueError("Invalid result count or spacing buffer")
    if not_before is not None and not_before.tzinfo is None:
        raise ValueError("not_before must be timezone-aware")

    target = next((item for item in commitments if item.get("id") == target_id), None)
    if target is None:
        raise ValueError("Commitment not found")
    if target.get("scheduling_mode", "fixed") != "flexible":
        return []
    if target.get("status") in ("canceled", "completed"):
        return []

    original_start = parse_dt(target["start"]).astimezone(timezone.utc)
    original_end = parse_dt(target["end"]).astimezone(timezone.utc)
    duration = original_end - original_start
    if not timedelta(0) < duration <= timedelta(hours=12):
        return []

    busy = []
    for other in commitments:
        if other.get("id") == target_id or other.get("status") in ("canceled", "completed"):
            continue
        try:
            first = parse_dt(other["start"]).astimezone(timezone.utc)
            last = parse_dt(other["end"]).astimezone(timezone.utc)
        except (ValueError, TypeError, KeyError):
            continue
        if last <= first:
            continue
        spacing = (buffer_minutes if (target.get("requires_travel")
                                     or other.get("requires_travel")) else 0)
        busy.append((first - timedelta(minutes=spacing),
                     last + timedelta(minutes=spacing)))

    date_anchor = original_start.astimezone(MICHIGAN).date()
    earliest = not_before.astimezone(timezone.utc) if not_before else None
    candidates = []
    for offset in range(days_ahead):
        day = date_anchor + timedelta(days=offset)
        for minute in range(earliest_hour * 60, latest_hour * 60, step_minutes):
            clock = time(minute // 60, minute % 60)
            try:
                local_start = _wall_time(day, clock)
                local_end_limit = _wall_time(day, time(latest_hour))
            except ValueError:
                continue
            start_utc = local_start.astimezone(timezone.utc)
            end_utc = start_utc + duration
            if end_utc > local_end_limit.astimezone(timezone.utc):
                continue
            if start_utc == original_start or (earliest and start_utc < earliest):
                continue
            if any(start_utc < occupied_end and occupied_start < end_utc
                   for occupied_start, occupied_end in busy):
                continue
            new_end = end_utc.astimezone(MICHIGAN)
            candidates.append({
                "start": local_start.isoformat(),
                "end": new_end.isoformat(),
                "shift_minutes": int((start_utc - original_start).total_seconds() // 60),
            })

    candidates.sort(key=lambda item: (
        abs(item["shift_minutes"]), item["shift_minutes"] < 0, item["start"]))
    return candidates[:max_results]


def answer_with_rules(
    question: str, commitments: list[dict[str, Any]], *,
    now: datetime | None = None,
) -> str:
    """Answer a few explicit planner questions without an AI call.

    This deliberately does not pretend to understand arbitrary language. It
    reads only the supplied workspace records and never claims live OU access.
    """
    from kin_core import detect_internal_conflicts, find_free_windows

    q = (question or "").strip().lower()
    if not 3 <= len(q) <= 500:
        raise ValueError("Enter a question between 3 and 500 characters")
    reference = now or datetime.now(MICHIGAN)
    if reference.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    reference = reference.astimezone(MICHIGAN)
    live = [
        c for c in commitments
        if c.get("status") not in ("canceled", "completed")
    ]
    if any(token in q for token in ("conflict", "clash", "overlap")):
        collisions = detect_internal_conflicts(live)
        if not collisions:
            return ("No overlapping commitments detected in this workspace. "
                    "KIN does not check other calendars or university systems.")
        rows = [f"- {c['a']} overlaps {c['b']}" for c in collisions[:5]]
        return ("Detected scheduling overlaps (rule-based, not AI):\n" +
                "\n".join(rows) +
                "\nMark a movable commitment as Flexible, then open Resolve conflicts.")

    if any(token in q for token in ("weather", "storm", "cancel", "closure", "closed")):
        return ("KIN cannot confirm university class cancellations. Check the "
                "Michigan Weather panel and Oakland University's official "
                "campus closings page before making decisions.")

    if any(token in q for token in ("free", "available", "open slot", "spare time")):
        day = reference + (timedelta(days=1) if "tomorrow" in q else timedelta(0))
        windows = find_free_windows(live, day, minimum_minutes=30)
        if not windows:
            return ("No free windows of at least 30 minutes were found between "
                    "8 AM and 10 PM in this workspace.")
        parts = []
        for window in windows[:5]:
            a = parse_dt(window["start"]).astimezone(MICHIGAN)
            b = parse_dt(window["end"]).astimezone(MICHIGAN)
            parts.append(f"- {a:%I:%M %p}–{b:%I:%M %p}")
        return ("Available windows (stored workspace only; travel not verified):\n"
                + "\n".join(parts))

    if any(token in q for token in ("move", "reschedule", "change time", "rearrange")):
        return ("Open Planner → Resolve conflicts for no-cost, rule-checked "
                "alternatives. KIN proposes times; you approve any change.")

    if any(token in q for token in ("schedule", "today", "tomorrow", "next",
                                   "class", "exam", "work", "meeting", "plan")):
        day = reference.date() + timedelta(days=1) if "tomorrow" in q else None
        items = []
        for c in live:
            try:
                start = parse_dt(c["start"]).astimezone(MICHIGAN)
            except (KeyError, ValueError, TypeError):
                continue
            if day is not None and start.date() != day:
                continue
            if day is None and start < reference:
                continue
            if "class" in q and c.get("event_type") != "class":
                continue
            items.append((start, c))
        items.sort(key=lambda pair: pair[0])
        if not items:
            return ("No matching upcoming commitments found in this workspace. "
                    "Other university calendars are not connected.")
        lines = [f"- {stamp:%a %b %d, %I:%M %p}: {item['title']}"
                 for stamp, item in items[:5]]
        return ("Upcoming entries from your stored timetable:\n" + "\n".join(lines))

    return ("Free-first KIN can answer questions about upcoming commitments, "
            "conflicts, available time, and how to reschedule. For open-ended "
            "conversation, an optional AI provider must be configured.")
