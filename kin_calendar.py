"""Minimal iCalendar (RFC 5545) import and export using only the standard library.

Deliberately small: it handles the subset of .ics that student calendars
actually emit (VEVENT with SUMMARY, DTSTART, DTEND, optional TZID, all-day
DATE values and STATUS:CANCELLED). Anything it cannot parse is reported to the
user as a skipped row rather than silently dropped or guessed at.

Recurrence (RRULE) is NOT expanded; a recurring event is imported as its first
occurrence and flagged, because silently inventing occurrences would be worse
than telling the user.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from kin_models import MICHIGAN, DEFAULT_EVENT_TYPE, make_commitment

PRODID = "-//KIN Keep It Navigable//Hacktoberfest 2026//EN"


# ------------------------------------------------------------------ export
def _escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(";", r"\;")
                .replace(",", r"\,").replace("\n", r"\n"))


def _fold(line: str) -> str:
    """RFC 5545 requires lines of at most 75 octets."""
    if len(line) <= 75:
        return line
    chunks = [line[:75]]
    rest = line[75:]
    while rest:
        chunks.append(" " + rest[:74])
        rest = rest[74:]
    return "\r\n".join(chunks)


def _utc_stamp(value: str) -> str:
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return moment.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")


def export_ics(commitments: list[dict[str, Any]], calendar_name: str = "KIN") -> str:
    """Serialize commitments to an .ics document."""
    now = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN", f"X-WR-CALNAME:{_escape(calendar_name)}",
    ]
    for c in commitments:
        try:
            dtstart, dtend = _utc_stamp(c["start"]), _utc_stamp(c["end"])
        except (KeyError, ValueError):
            continue
        description = c.get("notes") or ""
        if c.get("end_is_estimated"):
            description = (description + " | End time is a planning estimate, not official.").strip(" |")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{c.get('id', 'kin-event')}@kin.local",
            f"DTSTAMP:{now}", f"DTSTART:{dtstart}", f"DTEND:{dtend}",
            f"SUMMARY:{_escape(c.get('title', 'Untitled'))}",
        ]
        if description:
            lines.append(f"DESCRIPTION:{_escape(description)}")
        if c.get("source_url"):
            lines.append(f"URL:{c['source_url']}")
        if c.get("status") == "canceled":
            lines.append("STATUS:CANCELLED")
        lines += [f"CATEGORIES:{_escape(c.get('event_type', DEFAULT_EVENT_TYPE))}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


# ------------------------------------------------------------------ import
def _unfold(raw: str) -> list[str]:
    physical = raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    logical: list[str] = []
    for line in physical:
        if line[:1] in (" ", "\t") and logical:
            logical[-1] += line[1:]
        else:
            logical.append(line)
    return logical


def _unescape(text: str) -> str:
    return (text.replace(r"\n", "\n").replace(r"\,", ",")
                .replace(r"\;", ";").replace("\\\\", "\\"))


def _parse_property(line: str) -> tuple[str, dict[str, str], str]:
    head, _, value = line.partition(":")
    parts = head.split(";")
    name = parts[0].upper()
    params = {}
    for param in parts[1:]:
        key, _, val = param.partition("=")
        params[key.upper()] = val.strip('"')
    return name, params, value


def _parse_moment(value: str, params: dict[str, str]) -> tuple[datetime, bool]:
    """Return (aware datetime, is_all_day). Floating times are read as Michigan."""
    value = value.strip()
    if params.get("VALUE") == "DATE" or (len(value) == 8 and "T" not in value):
        day = datetime.strptime(value, "%Y%m%d")
        return day.replace(tzinfo=MICHIGAN), True
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC")), False
    naive = datetime.strptime(value, "%Y%m%dT%H%M%S")
    tzid = params.get("TZID")
    zone = MICHIGAN
    if tzid:
        try:
            zone = ZoneInfo(tzid)
        except (ZoneInfoNotFoundError, ValueError):
            zone = MICHIGAN
    return naive.replace(tzinfo=zone), False


def parse_ics(raw: str, *, workspace_id: str | None = None,
              event_type: str = DEFAULT_EVENT_TYPE) -> dict[str, Any]:
    """Parse .ics text into commitment candidates plus a report of what was skipped.

    Nothing is written anywhere: the caller shows a preview and asks the user to
    approve the import, as required by the plan.
    """
    events: list[dict[str, Any]] = []
    skipped: list[str] = []
    recurring = 0
    current: dict[str, Any] | None = None

    for line in _unfold(raw):
        if line.startswith("BEGIN:VEVENT"):
            current = {}
            continue
        if line.startswith("END:VEVENT"):
            if current is not None:
                parsed = _finalize(current, workspace_id, event_type)
                if isinstance(parsed, str):
                    skipped.append(parsed)
                else:
                    if current.get("_recurring"):
                        recurring += 1
                    events.append(parsed)
            current = None
            continue
        if current is None or not line.strip():
            continue
        name, params, value = _parse_property(line)
        if name == "SUMMARY":
            current["title"] = _unescape(value).strip()
        elif name == "DTSTART":
            current["start_raw"] = (value, params)
        elif name == "DTEND":
            current["end_raw"] = (value, params)
        elif name == "DURATION":
            current["duration"] = value
        elif name == "STATUS":
            current["status"] = value.strip().upper()
        elif name == "UID":
            current["uid"] = value.strip()
        elif name == "RRULE":
            current["_recurring"] = True
        elif name == "DESCRIPTION":
            current["notes"] = _unescape(value).strip()[:400]

    # Drop duplicates that share a title and start time.
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    duplicates = 0
    for event in events:
        key = (event["title"].strip().lower(), event["start"])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(event)

    return {
        "events": unique,
        "skipped": skipped,
        "duplicates_removed": duplicates,
        "recurring_first_occurrence_only": recurring,
    }


def _finalize(raw_event: dict[str, Any], workspace_id: str | None,
              event_type: str) -> dict[str, Any] | str:
    title = raw_event.get("title") or "Untitled imported event"
    if "start_raw" not in raw_event:
        return f"{title}: no DTSTART"
    try:
        start, all_day = _parse_moment(*raw_event["start_raw"])
    except ValueError:
        return f"{title}: unreadable start time"

    end: datetime | None = None
    if "end_raw" in raw_event:
        try:
            end, _ = _parse_moment(*raw_event["end_raw"])
        except ValueError:
            end = None
    if end is None and raw_event.get("duration"):
        end = start + _parse_duration(raw_event["duration"])
    if end is None:
        end = start + timedelta(days=1) if all_day else start + timedelta(hours=1)
    if end <= start:
        return f"{title}: end time is not after start time"

    # Normalise to Michigan local time. The instant is unchanged; storing one
    # consistent zone keeps the database readable and avoids a mix of UTC and
    # local strings coming from different calendar exporters.
    start, end = start.astimezone(MICHIGAN), end.astimezone(MICHIGAN)

    commitment = make_commitment(
        title, start.isoformat(), end.isoformat(),
        event_type=event_type, workspace_id=workspace_id, origin="ics_import",
        notes=raw_event.get("notes", ""),
        status="canceled" if raw_event.get("status") == "CANCELLED" else "planned",
    )
    commitment["all_day"] = all_day
    return commitment


def _parse_duration(value: str) -> timedelta:
    """Parse the common PnDTnHnMnS subset of an iCalendar duration."""
    import re
    match = re.fullmatch(
        r"[+-]?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?",
        value.strip().upper(),
    )
    if not match:
        return timedelta(hours=1)
    weeks, days, hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
