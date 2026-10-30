"""Pure, auditable schedule logic. The LLM never determines overlap or official status.

Every function here is deterministic and side-effect free. If a result appears
in the user interface as a fact, it was computed in this module, not generated
by a language model.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from kin_models import (
    DEFAULT_EVENT_TYPE,
    EVENT_TYPES,
    MICHIGAN,
    event_type_meta,
    michigan_offset_for,
)

# Ordering used to rank which weather alert matters most for a commitment.
SEVERITY_RANK = {"Extreme": 4, "Severe": 3, "Moderate": 2, "Minor": 1, "Unknown": 0}


def parse_dt(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Datetime must include a time-zone offset")
    return result


def overlaps(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    """Half-open interval overlap: events that merely touch do not conflict."""
    a0, a1, b0, b1 = map(parse_dt, (start_a, end_a, start_b, end_b))
    if a1 <= a0 or b1 <= b0:
        raise ValueError("End must be after start")
    return a0 < b1 and b0 < a1


def effective_window(event: dict[str, Any], commute_minutes: int = 0) -> tuple[str, str]:
    """Approximate buffer for a commitment. NOT a prediction of travel safety/time."""
    if not 0 <= commute_minutes <= 180:
        raise ValueError("Commute must be between 0 and 180 minutes")
    start = parse_dt(event["start"]) - timedelta(minutes=commute_minutes)
    end = parse_dt(event["end"])
    return start.isoformat(), end.isoformat()


def michigan_offset_matches(value: str) -> bool:
    """True when the offset in an ISO string is the real Michigan offset that date.

    Catches a model that emits -05:00 for an October date that is actually EDT.
    A datetime expressed in any other zone (for example UTC) that resolves to
    the same instant is accepted, because the instant is unambiguous.
    """
    moment = parse_dt(value)
    expected = michigan_offset_for(moment.astimezone(MICHIGAN).replace(tzinfo=None))
    actual_seconds = int((moment.utcoffset() or timedelta(0)).total_seconds())
    sign = "+" if actual_seconds >= 0 else "-"
    magnitude = abs(actual_seconds)
    actual = f"{sign}{magnitude // 3600:02d}:{(magnitude % 3600) // 60:02d}"
    return actual in (expected, "+00:00")


def assess_alerts(events: list[dict], alerts: list[dict], commute_minutes: int) -> list[dict]:
    """Match weather alert windows against commitment windows plus travel buffer.

    At most one impact is returned per (commitment, alert name) pair; when the
    same alert is reissued the most severe instance wins.
    """
    best: dict[tuple[str, str], dict] = {}
    for event in events:
        if event.get("status") in ("canceled", "completed"):
            continue
        travel = event.get("requires_travel", True)
        start, end = effective_window(event, commute_minutes if travel else 0)
        for alert in alerts:
            onset = alert.get("onset") or alert.get("effective")
            finish = alert.get("ends") or alert.get("expires")
            if not onset or not finish:
                continue
            try:
                matched = overlaps(start, end, onset, finish)
            except ValueError:
                continue
            if not matched:
                continue
            name = alert.get("event", "Weather alert")
            severity = alert.get("severity", "Unknown")
            impact = {
                "event_id": event["id"],
                "commitment": event["title"],
                "commitment_start": event["start"],
                "alert": name,
                "severity": severity,
                "source_url": alert.get("source_url", "https://www.weather.gov/"),
                "is_simulation": bool(alert.get("is_simulation", False)),
                "buffer_applied_minutes": commute_minutes if travel else 0,
                "reason": "The warning's reported time window overlaps the commitment or its "
                          "user-selected preparation/commute buffer.",
                "status": "Possible weather-related impact; no university cancellation inferred.",
            }
            key = (event["id"], name)
            previous = best.get(key)
            if previous is None or SEVERITY_RANK.get(severity, 0) > SEVERITY_RANK.get(
                previous["severity"], 0
            ):
                best[key] = impact
    return sorted(best.values(), key=lambda i: i["commitment_start"])


def assess_opportunities(
    commitments: list[dict], opportunities: list[dict], buffer_minutes: int = 30
) -> list[dict]:
    """Use sample/planning buffers, not verified travel-duration claims."""
    result = []
    for opportunity in opportunities:
        opp_start = parse_dt(opportunity["start"]) - timedelta(minutes=buffer_minutes)
        opp_end = parse_dt(opportunity["end"]) + timedelta(minutes=buffer_minutes)
        conflicts = [
            e["title"]
            for e in commitments
            if e.get("status") not in ("canceled", "completed")
            and overlaps(opp_start.isoformat(), opp_end.isoformat(), e["start"], e["end"])
        ]
        # An unknown end time cannot be assessed as confidently as a known one.
        certainty = "estimated_end" if opportunity.get("end_is_estimated") else "known_end"
        result.append({
            **opportunity,
            "conflicts": conflicts,
            "fits": not conflicts,
            "buffer_minutes": buffer_minutes,
            "certainty": certainty,
        })
    return result


def validate_event_proposal(data: dict, *, strict_michigan: bool = False) -> dict:
    """Strict trust boundary for LLM-extracted dates before user approval."""
    if not isinstance(data, dict):
        raise ValueError("Expected event data object")
    title = data.get("title")
    if not isinstance(title, str) or not 3 <= len(title.strip()) <= 100:
        raise ValueError("Event title is missing or too long")
    if not isinstance(data.get("start"), str) or not isinstance(data.get("end"), str):
        raise ValueError("Both event times must be present")
    a, b = parse_dt(data["start"]), parse_dt(data["end"])
    if not (a < b) or b - a > timedelta(hours=24):
        raise ValueError("Invalid event duration")
    if not isinstance(data.get("requires_travel"), bool):
        raise ValueError("requires_travel must be a boolean")
    if strict_michigan:
        for field in ("start", "end"):
            if not michigan_offset_matches(data[field]):
                raise ValueError(
                    f"The {field} offset is not the correct America/Detroit offset for that date"
                )
    event_type = data.get("event_type")
    if event_type not in EVENT_TYPES:
        event_type = DEFAULT_EVENT_TYPE
    return {
        "title": title.strip(),
        "start": a.isoformat(),
        "end": b.isoformat(),
        "requires_travel": data["requires_travel"],
        "event_type": event_type,
    }


def detect_internal_conflicts(commitments: list[dict]) -> list[dict]:
    """Commitment-vs-commitment overlaps inside the user's own timetable."""
    live = [c for c in commitments if c.get("status") not in ("canceled", "completed")]
    found = []
    for i, first in enumerate(live):
        for second in live[i + 1:]:
            try:
                if overlaps(first["start"], first["end"], second["start"], second["end"]):
                    found.append({
                        "a_id": first["id"], "b_id": second["id"],
                        "a": first["title"], "b": second["title"],
                        "start": min(first["start"], second["start"]),
                    })
            except ValueError:
                continue
    return found


def find_free_windows(
    commitments: list[dict], day: datetime, *, earliest_hour: int = 8, latest_hour: int = 22,
    minimum_minutes: int = 45,
) -> list[dict]:
    """Gaps on one local day that are long enough to be worth offering."""
    day_start = day.replace(hour=earliest_hour, minute=0, second=0, microsecond=0)
    day_end = day.replace(hour=latest_hour, minute=0, second=0, microsecond=0)
    busy = []
    for c in commitments:
        if c.get("status") in ("canceled", "completed"):
            continue
        try:
            start, end = parse_dt(c["start"]), parse_dt(c["end"])
        except (ValueError, KeyError):
            continue
        start, end = start.astimezone(MICHIGAN), end.astimezone(MICHIGAN)
        if end > day_start and start < day_end:
            busy.append((max(start, day_start), min(end, day_end)))
    busy.sort()
    windows, cursor = [], day_start
    for start, end in busy:
        if (start - cursor) >= timedelta(minutes=minimum_minutes):
            windows.append({"start": cursor.isoformat(), "end": start.isoformat()})
        cursor = max(cursor, end)
    if (day_end - cursor) >= timedelta(minutes=minimum_minutes):
        windows.append({"start": cursor.isoformat(), "end": day_end.isoformat()})
    return windows


def simulate_change(
    commitments: list[dict], *, add: dict | None = None, move_id: str | None = None,
    shift_minutes: int = 0, remove_id: str | None = None, buffer_minutes: int = 0,
) -> dict[str, Any]:
    """Future-Self Simulator (plan Module Q): compute a hypothetical, apply nothing.

    Returns the before/after conflict sets so the caller can show a diff and ask
    the user whether to apply it. This function never mutates its input.
    """
    before = detect_internal_conflicts(commitments)
    projected = [dict(c) for c in commitments]
    if remove_id:
        projected = [c for c in projected if c["id"] != remove_id]
    if move_id and shift_minutes:
        for c in projected:
            if c["id"] == move_id:
                c["start"] = (parse_dt(c["start"]) + timedelta(minutes=shift_minutes)).isoformat()
                c["end"] = (parse_dt(c["end"]) + timedelta(minutes=shift_minutes)).isoformat()
    if add:
        candidate = dict(add)
        if buffer_minutes and candidate.get("requires_travel", True):
            candidate = {
                **candidate,
                "start": (parse_dt(candidate["start"])
                          - timedelta(minutes=buffer_minutes)).isoformat(),
            }
        projected.append(candidate)
    after = detect_internal_conflicts(projected)
    before_keys = {tuple(sorted((c["a"], c["b"]))) for c in before}
    after_keys = {tuple(sorted((c["a"], c["b"]))) for c in after}
    return {
        "before_conflicts": before,
        "after_conflicts": after,
        "new_conflicts": [c for c in after if tuple(sorted((c["a"], c["b"]))) not in before_keys],
        "resolved_conflicts": [c for c in before
                               if tuple(sorted((c["a"], c["b"]))) not in after_keys],
        "net_change": len(after) - len(before),
        "applied": False,
    }


def sample_commitments() -> list[dict]:
    """Fictional demonstration timetable. No real student record is ever loaded."""
    return [
        {"id": "study-group", "title": "Study group (fictional)", "event_type": "study",
         "start": "2026-10-30T15:30:00-04:00", "end": "2026-10-30T16:30:00-04:00",
         "requires_travel": False, "origin": "sample", "status": "planned"},
        {"id": "exam", "title": "Morning exam (fictional)", "event_type": "exam",
         "start": "2026-10-31T09:00:00-04:00", "end": "2026-10-31T10:30:00-04:00",
         "requires_travel": True, "origin": "sample", "status": "planned"},
    ]


def simulated_alert() -> dict:
    """A reproducible demonstration alert. Always carries is_simulation = True."""
    return {
        "event": "SIMULATED Winter Storm Warning",
        "severity": "Severe",
        "onset": "2026-10-31T06:30:00-04:00",
        "ends": "2026-10-31T12:00:00-04:00",
        "source_url": "https://www.weather.gov/",
        "is_simulation": True,
        "status": "DEMO_ONLY",
        "headline": "DEMONSTRATION ONLY — this warning was generated by KIN, not by the NWS.",
    }
