"""Load a fictional student-life dataset into the local store.

The dataset is authored as plain local wall-clock times with NO UTC offset.
This module attaches America/Detroit and lets zoneinfo derive the correct
offset per date, which is why the data stays correct across the 1 November 2026
daylight-saving change instead of hard-coding -04:00.

Nothing here reaches the network or a model. Every row is validated and bad
rows are reported to the caller rather than silently defaulted, so a malformed
file is visible instead of quietly wrong.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from kin_models import (
    COMMITMENT_STATUSES, EVENT_TYPES, MICHIGAN, DEFAULT_PREFERENCES,
    make_commitment, make_workspace,
)

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_DATASET = DATA_DIR / "KIN_Fictional_Student_Life_Dataset.json"

#: Weekday codes used by the dataset, mapped to Python's Monday=0 convention.
WEEKDAYS = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}

WORKSPACE_KINDS = ("Personal", "University", "Course", "Research",
                   "Employment", "Family", "Sports", "Gaming", "Other")

#: The dataset is written relative to this demonstration "today".
REFERENCE_NOW = datetime(2026, 10, 30, tzinfo=MICHIGAN)


class SeedError(ValueError):
    """The dataset file is unusable as a whole."""


def _localize(value: str, field: str, label: str, problems: list[str]) -> datetime | None:
    """Parse a naive local time and attach America/Detroit.

    An explicit offset in the file is accepted but reported, because the author
    was asked not to supply one and getting it wrong is the main failure mode.
    """
    try:
        moment = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        problems.append(f"{label}: unreadable {field} {value!r}")
        return None
    if moment.tzinfo is not None:
        problems.append(f"{label}: {field} already carried an offset; "
                        "KIN re-derived it for America/Detroit")
        return moment.astimezone(MICHIGAN)
    return moment.replace(tzinfo=MICHIGAN)


def _clean_type(value: Any, label: str, problems: list[str]) -> str:
    if value in EVENT_TYPES:
        return value
    problems.append(f"{label}: unknown event_type {value!r}, stored as 'personal'")
    return "personal"


def _derive_status(end: datetime, declared: Any, label: str,
                   problems: list[str]) -> str:
    """Trust a valid declared status; otherwise infer from the reference date."""
    if declared in COMMITMENT_STATUSES:
        return declared
    if declared is not None:
        problems.append(f"{label}: unknown status {declared!r}, inferred instead")
    return "completed" if end < REFERENCE_NOW else "planned"


def parse_dataset(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate and expand a dataset into records ready for the store.

    Returns the profile, workspaces, expanded commitments and a list of
    human-readable problems. Raises SeedError only when the file is structurally
    unusable.
    """
    if not isinstance(raw, dict):
        raise SeedError("The dataset must be a JSON object")
    for key in ("profile", "workspaces"):
        if not isinstance(raw.get(key), (dict, list)):
            raise SeedError(f"The dataset is missing its '{key}' section")

    problems: list[str] = []

    # ----------------------------------------------------------- workspaces
    workspaces: list[dict[str, Any]] = []
    for entry in raw.get("workspaces", []):
        name = str(entry.get("name", "")).strip()
        if not name:
            problems.append("a workspace had no name and was skipped")
            continue
        kind = entry.get("kind")
        if kind not in WORKSPACE_KINDS:
            problems.append(f"workspace {name}: unknown kind {kind!r}, stored as 'Other'")
            kind = "Other"
        workspaces.append(make_workspace(name, kind, entry.get("assistant_alias")))
    if not workspaces:
        raise SeedError("The dataset defined no usable workspaces")
    by_name = {w["name"]: w for w in workspaces}

    def resolve(entry: dict, label: str) -> dict:
        wanted = entry.get("workspace")
        target = by_name.get(wanted)
        if target is None:
            problems.append(f"{label}: unknown workspace {wanted!r}, "
                            f"placed in {workspaces[0]['name']}")
            return workspaces[0]
        return target

    commitments: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(record: dict[str, Any]) -> None:
        key = (record["workspace_id"], record["title"].strip().lower(), record["start"])
        if key in seen:
            return
        seen.add(key)
        commitments.append(record)

    # ------------------------------------------------------------- recurring
    for index, pattern in enumerate(raw.get("recurring", [])):
        label = f"recurring[{index}] {pattern.get('title', '?')}"
        workspace = resolve(pattern, label)
        try:
            first = datetime.fromisoformat(str(pattern["from_date"])).date()
            last = datetime.fromisoformat(str(pattern["to_date"])).date()
        except (KeyError, TypeError, ValueError):
            problems.append(f"{label}: unreadable from_date/to_date, pattern skipped")
            continue
        if last < first:
            problems.append(f"{label}: to_date precedes from_date, pattern skipped")
            continue
        wanted_days = {WEEKDAYS[code] for code in pattern.get("days", [])
                       if code in WEEKDAYS}
        if not wanted_days:
            problems.append(f"{label}: no recognised weekday codes, pattern skipped")
            continue
        start_clock, end_clock = pattern.get("start_time"), pattern.get("end_time")
        event_type = _clean_type(pattern.get("event_type"), label, problems)
        requires_travel = bool(pattern.get("requires_travel",
                                           EVENT_TYPES[event_type]["travel"]))
        day = first
        made = 0
        while day <= last:
            if day.weekday() in wanted_days:
                start = _localize(f"{day}T{start_clock}", "start_time", label, problems)
                end = _localize(f"{day}T{end_clock}", "end_time", label, problems)
                if start is None or end is None:
                    break
                if end <= start:
                    problems.append(f"{label}: end_time is not after start_time, skipped")
                    break
                add(make_commitment(
                    str(pattern.get("title", "Untitled")), start.isoformat(),
                    end.isoformat(), event_type=event_type,
                    requires_travel=requires_travel, workspace_id=workspace["id"],
                    origin="seed:recurring",
                    status=_derive_status(end, None, label, problems),
                    notes=str(pattern.get("notes", ""))[:400]))
                made += 1
            day += timedelta(days=1)
        if made == 0:
            problems.append(f"{label}: produced no occurrences")

    # -------------------------------------------------------------- one-off
    for index, entry in enumerate(raw.get("one_off", [])):
        label = f"one_off[{index}] {entry.get('title', '?')}"
        workspace = resolve(entry, label)
        start = _localize(str(entry.get("start")), "start", label, problems)
        end = _localize(str(entry.get("end")), "end", label, problems)
        if start is None or end is None:
            continue
        if end <= start:
            problems.append(f"{label}: end is not after start, skipped")
            continue
        if end - start > timedelta(hours=24):
            problems.append(f"{label}: longer than 24 hours, skipped")
            continue
        event_type = _clean_type(entry.get("event_type"), label, problems)
        add(make_commitment(
            str(entry.get("title", "Untitled")), start.isoformat(), end.isoformat(),
            event_type=event_type,
            requires_travel=bool(entry.get("requires_travel",
                                           EVENT_TYPES[event_type]["travel"])),
            workspace_id=workspace["id"], origin="seed:one_off",
            status=_derive_status(end, entry.get("status"), label, problems),
            notes=str(entry.get("notes", ""))[:400]))

    if not commitments:
        raise SeedError("The dataset produced no usable commitments")

    # ------------------------------------------------------------- profile
    profile = raw.get("profile", {}) or {}
    preferences = {key: profile[key] for key in DEFAULT_PREFERENCES if key in profile}

    commitments.sort(key=lambda c: c["start"])
    return {
        "profile": profile,
        "preferences": preferences,
        "workspaces": workspaces,
        "commitments": commitments,
        "problems": problems,
    }


def load_file(path: Path | str | None = None) -> dict[str, Any]:
    target = Path(path) if path else DEFAULT_DATASET
    if not target.exists():
        raise SeedError(f"No dataset file at {target}")
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SeedError(f"The dataset is not valid JSON: {exc}") from exc
    parsed = parse_dataset(raw)
    parsed["source_file"] = target.name
    return parsed


def install(store, parsed: dict[str, Any], *, replace: bool = True) -> dict[str, Any]:
    """Write a parsed dataset into the store.

    `store` is passed in rather than imported so tests can supply an isolated
    module instance. With replace=True the existing local data is erased first,
    which is what a demonstration reset should do.
    """
    if replace:
        store.erase_all()
    for workspace in parsed["workspaces"]:
        store.add_workspace(workspace)
    for commitment in parsed["commitments"]:
        store.save_commitment(commitment)
    if parsed["preferences"]:
        store.set_preferences(parsed["preferences"])
    return {
        "workspaces": len(parsed["workspaces"]),
        "commitments": len(parsed["commitments"]),
        "problems": parsed["problems"],
        "first": parsed["commitments"][0]["start"][:10],
        "last": parsed["commitments"][-1]["start"][:10],
    }


def dataset_available(path: Path | str | None = None) -> bool:
    return (Path(path) if path else DEFAULT_DATASET).exists()
