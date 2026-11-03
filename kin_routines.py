"""Deterministic editing and cancellation of KIN manual routine occurrences.

No external calendar writes. Edits are previews until an explicit approval; the
storage layer verifies the originals before applying all replacements atomically.
"""
from __future__ import annotations

from datetime import time, timedelta, timezone
from typing import Any

from kin_core import detect_internal_conflicts, parse_dt
from kin_life import SCHEDULING_MODES, _wall_time
from kin_models import MICHIGAN

EDIT_SCOPES = ("This occurrence", "This and later", "Entire series")


def cross_workspace_conflicts(commitments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only overlaps crossing two KIN workspaces in the current profile.

    Excludes entries without an identifiable workspace; these are not evidence
    that two different workspaces conflicted.
    """
    by_id = {c.get("id"): c for c in commitments if c.get("id")}
    result = []
    for pair in detect_internal_conflicts(commitments):
        left, right = by_id.get(pair["a_id"]), by_id.get(pair["b_id"])
        if not left or not right:
            continue
        a_ws, b_ws = left.get("workspace_id"), right.get("workspace_id")
        if a_ws and b_ws and a_ws != b_ws:
            result.append({**pair, "a_workspace_id": a_ws, "b_workspace_id": b_ws})
    return result


def _select_scope(
    commitments: list[dict[str, Any]], target_id: str, scope: str
) -> list[dict[str, Any]]:
    if scope not in EDIT_SCOPES:
        raise ValueError("Unsupported edit scope")
    target = next((c for c in commitments if c.get("id") == target_id), None)
    if target is None:
        raise ValueError("Commitment no longer exists")
    if target.get("origin") != "manual":
        raise ValueError("Only manually created KIN commitments can be edited in this view")
    if scope == "This occurrence":
        return [target]
    series = target.get("series_id")
    if not series:
        raise ValueError("This commitment is not part of a recurring series")
    start = parse_dt(target["start"]).astimezone(timezone.utc)
    selected = [
        c for c in commitments
        if c.get("origin") == "manual"
        and c.get("workspace_id") == target.get("workspace_id")
        and c.get("series_id") == series
        and (scope == "Entire series"
             or parse_dt(c["start"]).astimezone(timezone.utc) >= start)
    ]
    if not selected:
        raise ValueError("No matching occurrences found")
    return sorted(selected, key=lambda c: parse_dt(c["start"]))


def preview_routine_changes(
    commitments: list[dict[str, Any]],
    target_id: str,
    scope: str,
    *,
    title: str = "",
    start_time: time | None = None,
    end_time: time | None = None,
    mode: str | None = None,
    notes: str | None = None,
    cancel: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (original, proposed) without mutating inputs.

    A series edit changes time-of-day per occurrence while retaining each date.
    This preserves weekday/weekly rules and DST validity without guessing.
    Canceled occurrences remain in the archive and do not block free slots.
    """
    originals = _select_scope(commitments, target_id, scope)
    if not cancel:
        if not 1 <= len(title.strip()) <= 100:
            raise ValueError("Title must be 1–100 characters")
        if not isinstance(start_time, time) or not isinstance(end_time, time):
            raise ValueError("Both start and end times are required")
        if mode not in SCHEDULING_MODES:
            raise ValueError("Invalid scheduling mode")
        if notes is not None and len(notes) > 2000:
            raise ValueError("Notes must be 2,000 characters or less")

    proposed: list[dict[str, Any]] = []
    for original in originals:
        candidate = dict(original)
        if cancel:
            candidate["status"] = "canceled"
        else:
            day = parse_dt(original["start"]).astimezone(MICHIGAN).date()
            start = _wall_time(day, start_time)
            end = _wall_time(day, end_time)
            duration = end.astimezone(timezone.utc) - start.astimezone(timezone.utc)
            if not timedelta(0) < duration <= timedelta(hours=24):
                raise ValueError("End time must follow start time on the same day")
            candidate.update(
                title=title.strip(), start=start.isoformat(), end=end.isoformat(),
                scheduling_mode=mode, notes=notes if notes is not None else original.get("notes", "")
            )
        proposed.append(candidate)
    return [dict(c) for c in originals], proposed
