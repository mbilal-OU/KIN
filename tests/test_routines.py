"""Offline tests for user-approved recurring routine edits and workspace coordination."""
from copy import deepcopy
from datetime import date, time

import pytest

import kin_store
from kin_life import build_manual_occurrences
from kin_models import make_commitment
from kin_routines import (
    EDIT_SCOPES, cross_workspace_conflicts, preview_routine_changes,
)


@pytest.fixture()
def local_store(tmp_path):
    kin_store.set_db_path(tmp_path / "routine.db")
    kin_store.init_db()
    yield
    kin_store.set_db_path(None)


def routine(week=3, *, workspace_id="personal"):
    return build_manual_occurrences(
        "Read papers", date(2026, 11, 2), time(9), time(10),
        scheduling_mode="flexible", repeat="Every week",
        weeks=week, workspace_id=workspace_id)


def edit(rows, target, scope="This occurrence", **kwargs):
    return preview_routine_changes(
        rows, target["id"], scope,
        title="Focused study", start_time=time(11), end_time=time(12),
        mode="protected", notes="Private", **kwargs)


def test_edit_scope_preserves_all_other_occurrences():
    records = routine()
    untouched = deepcopy(records)
    old, new = edit(records, records[1])
    assert len(old) == len(new) == 1
    assert new[0]["title"] == "Focused study"
    assert new[0]["start"].startswith("2026-11-09T11:00")
    assert new[0]["scheduling_mode"] == "protected"
    assert records == untouched


def test_this_and_later_edits_future_only():
    records = routine()
    old, new = edit(records, records[1], scope="This and later")
    assert [c["id"] for c in old] == [c["id"] for c in records[1:]]
    assert len(new) == 2
    assert all(c["title"] == "Focused study" for c in new)


def test_entire_series_edits_all_occurrences():
    records = routine()
    old, new = edit(records, records[2], scope="Entire series")
    assert len(old) == 3
    assert all(c["start"].endswith("-05:00") for c in new)
    assert len({c["series_id"] for c in new}) == 1


def test_cancel_future_is_non_destructive():
    records = routine()
    original = deepcopy(records)
    old, canceled = preview_routine_changes(
        records, records[1]["id"], "This and later", cancel=True)
    assert len(old) == 2
    assert all(c["status"] == "canceled" for c in canceled)
    assert all(c["status"] == "planned" for c in records)
    assert records == original


def test_unrelated_or_imported_events_cannot_be_changed():
    record = make_commitment(
        "Imported", "2026-11-04T12:00:00-05:00",
        "2026-11-04T13:00:00-05:00", origin="ics_import")
    with pytest.raises(ValueError, match="manually"):
        edit([record], record)
    manual = routine(1)[0]
    with pytest.raises(ValueError, match="scope"):
        edit([manual], manual, scope="Everyone")
    record_without_series = dict(manual)
    record_without_series.pop("series_id")
    with pytest.raises(ValueError, match="series"):
        edit([record_without_series], record_without_series,
             scope="Entire series")


def test_edits_refuse_bad_time_and_do_not_silently_shift_dst():
    records = build_manual_occurrences(
        "Read", date(2026, 3, 1), time(9), time(10),
        repeat="Every week", weeks=3, scheduling_mode="flexible")
    with pytest.raises(ValueError, match="does not exist"):
        preview_routine_changes(
            records, records[0]["id"], "Entire series",
            title="Read", start_time=time(2, 30), end_time=time(3, 30),
            mode="flexible")
    with pytest.raises(ValueError, match="End time"):
        preview_routine_changes(
            records, records[0]["id"], "This occurrence",
            title="Read", start_time=time(16), end_time=time(15),
            mode="flexible")


def test_only_same_workspace_series_can_be_edited():
    original = routine(2, workspace_id="personal")
    foreign = dict(original[0])
    foreign["id"] = "foreign"
    foreign["workspace_id"] = "research"
    old, new = edit(original + [foreign], original[0], scope="Entire series")
    assert len(old) == len(new) == 2
    assert not any(c["id"] == "foreign" for c in new)


def test_cross_workspace_conflicts_only_reports_real_crossings():
    a = make_commitment(
        "Lab", "2026-11-05T10:00:00-05:00", "2026-11-05T12:00:00-05:00",
        workspace_id="University")
    b = make_commitment(
        "Shift", "2026-11-05T11:00:00-05:00", "2026-11-05T13:00:00-05:00",
        workspace_id="Work")
    c = make_commitment(
        "Study", "2026-11-05T11:30:00-05:00", "2026-11-05T12:30:00-05:00",
        workspace_id="University")
    result = cross_workspace_conflicts([a, b, c])
    assert len(result) == 2
    assert all(x["a_workspace_id"] != x["b_workspace_id"] for x in result)


def test_touching_cancelled_and_same_workspace_not_cross_conflicts():
    a = make_commitment(
        "Lab", "2026-11-05T10:00:00-05:00", "2026-11-05T11:00:00-05:00",
        workspace_id="University")
    b = make_commitment(
        "Shift", "2026-11-05T11:00:00-05:00", "2026-11-05T12:00:00-05:00",
        workspace_id="Work")
    c = make_commitment(
        "Canceled", "2026-11-05T10:30:00-05:00", "2026-11-05T12:00:00-05:00",
        workspace_id="Work", status="canceled")
    assert cross_workspace_conflicts([a, b, c]) == []


def test_atomic_save_verifies_stored_batch(local_store):
    records = routine()
    for c in records:
        kin_store.save_commitment(c)
    old, new = edit(records, records[0], scope="Entire series")
    assert kin_store.save_commitments_if_unchanged(old, new)
    stored = kin_store.list_commitments()
    assert len(stored) == 3
    assert all(c["title"] == "Focused study" for c in stored)
    assert all(c.get("scheduling_mode") == "protected" for c in stored)


def test_stale_preview_fails_without_partial_write(local_store):
    records = routine()
    for c in records:
        kin_store.save_commitment(c)
    old, new = edit(records, records[0], scope="Entire series")
    changed = dict(records[1])
    changed["notes"] = "Modified elsewhere"
    kin_store.save_commitment(changed)
    assert not kin_store.save_commitments_if_unchanged(old, new)
    stored = kin_store.list_commitments()
    assert stored[1]["notes"] == "Modified elsewhere"
    assert stored[0]["title"] == "Read papers"


def test_duplicate_rejection_is_atomic(local_store):
    records = routine(2)
    other = make_commitment(
        "Focused study", "2026-11-02T11:00:00-05:00",
        "2026-11-02T12:00:00-05:00", workspace_id="personal")
    for c in records + [other]:
        kin_store.save_commitment(c)
    old, new = edit(records + [other], records[0], scope="Entire series")
    assert not kin_store.save_commitments_if_unchanged(old, new)
    stored = kin_store.list_commitments()
    assert sum(c["title"] == "Read papers" for c in stored) == 2


def test_rejects_workspace_move_and_unknown_ids(local_store):
    rows = routine(1)
    kin_store.save_commitment(rows[0])
    old, new = edit(rows, rows[0])
    migrated = dict(new[0])
    migrated["workspace_id"] = "another"
    assert not kin_store.save_commitments_if_unchanged(old, [migrated])
    missing = dict(old[0])
    missing["id"] = "missing"
    assert not kin_store.save_commitments_if_unchanged([missing], new)


def test_cancel_series_persists_and_can_be_exported(local_store):
    rows = routine(2)
    for c in rows:
        kin_store.save_commitment(c)
    old, canceled = preview_routine_changes(
        rows, rows[0]["id"], "Entire series", cancel=True)
    assert kin_store.save_commitments_if_unchanged(old, canceled)
    exported = kin_store.export_all()
    assert len(exported["commitments"]) == 2
    assert all(c["status"] == "canceled" for c in exported["commitments"])
