"""Persistence, approval lifecycle and calendar interchange tests.

Each test gets its own throwaway database file, so nothing touches the real
kin_local.db and the suite needs no network access.
"""
import importlib
import json

import pytest

import kin_calendar
import kin_store
from kin_models import (
    ACTION_PROPOSED, ACTION_REJECTED, ACTION_VERIFIED, make_action, make_commitment,
    make_notification, make_workspace,
)


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """A fresh kin_store bound to an isolated SQLite file."""
    monkeypatch.setenv("KIN_DB_PATH", str(tmp_path / "test.db"))
    module = importlib.reload(kin_store)
    module.init_db()
    return module


@pytest.fixture()
def workspace(store):
    return store.ensure_default_workspace()


# ----------------------------------------------------------------- schema
def test_init_is_idempotent(store):
    store.init_db()
    store.init_db()
    assert store.list_workspaces() == []


def test_default_workspace_is_created_once(store):
    first = store.ensure_default_workspace()
    second = store.ensure_default_workspace()
    assert first["id"] == second["id"]
    assert len(store.list_workspaces()) == 1


# ------------------------------------------------------------ commitments
def test_save_and_read_back_a_commitment(store, workspace):
    record = make_commitment("Organic chemistry", "2026-10-30T10:00:00-04:00",
                             "2026-10-30T11:30:00-04:00", event_type="class",
                             workspace_id=workspace["id"])
    store.save_commitment(record)
    assert store.commitment_exists(record["id"])
    stored = store.list_commitments(workspace["id"])
    assert len(stored) == 1
    assert stored[0]["title"] == "Organic chemistry"
    assert stored[0]["event_type"] == "class"
    assert stored[0]["requires_travel"] is True


def test_commitments_are_returned_in_start_order(store, workspace):
    for title, start, end in [
        ("Late", "2026-10-30T18:00:00-04:00", "2026-10-30T19:00:00-04:00"),
        ("Early", "2026-10-30T08:00:00-04:00", "2026-10-30T09:00:00-04:00"),
        ("Middle", "2026-10-30T12:00:00-04:00", "2026-10-30T13:00:00-04:00"),
    ]:
        store.save_commitment(make_commitment(title, start, end,
                                              workspace_id=workspace["id"]))
    assert [c["title"] for c in store.list_commitments(workspace["id"])] == \
           ["Early", "Middle", "Late"]


def test_resaving_the_same_id_updates_instead_of_duplicating(store, workspace):
    record = make_commitment("Draft", "2026-10-30T10:00:00-04:00",
                             "2026-10-30T11:00:00-04:00", workspace_id=workspace["id"])
    store.save_commitment(record)
    record["title"] = "Renamed"
    record["status"] = "completed"
    store.save_commitment(record)
    stored = store.list_commitments(workspace["id"])
    assert len(stored) == 1
    assert stored[0]["title"] == "Renamed"
    assert stored[0]["status"] == "completed"


def test_duplicate_detection_matches_title_and_start(store, workspace):
    record = make_commitment("Volleyball", "2026-10-30T18:00:00-04:00",
                             "2026-10-30T20:00:00-04:00", workspace_id=workspace["id"])
    store.save_commitment(record)
    assert store.find_duplicate("Volleyball", record["start"], workspace["id"])
    assert store.find_duplicate("  Volleyball  ", record["start"], workspace["id"])
    assert store.find_duplicate("Volleyball", "2026-10-31T18:00:00-04:00",
                                workspace["id"]) is None
    assert store.find_duplicate("Basketball", record["start"], workspace["id"]) is None


def test_delete_removes_only_the_target(store, workspace):
    keep = make_commitment("Keep", "2026-10-30T10:00:00-04:00",
                           "2026-10-30T11:00:00-04:00", workspace_id=workspace["id"])
    drop = make_commitment("Drop", "2026-10-30T12:00:00-04:00",
                           "2026-10-30T13:00:00-04:00", workspace_id=workspace["id"])
    store.save_commitment(keep)
    store.save_commitment(drop)
    store.delete_commitment(drop["id"])
    assert not store.commitment_exists(drop["id"])
    assert [c["title"] for c in store.list_commitments(workspace["id"])] == ["Keep"]


# --------------------------------------------- workspace isolation (permissions)
def test_commitments_do_not_leak_between_workspaces(store):
    university = store.add_workspace(make_workspace("OU", "University", "Navi"))
    family = store.add_workspace(make_workspace("Our Home", "Family", "Helper"))
    store.save_commitment(make_commitment("Exam", "2026-10-31T09:00:00-04:00",
                                          "2026-10-31T10:30:00-04:00",
                                          workspace_id=university["id"]))
    store.save_commitment(make_commitment("School pickup", "2026-10-31T15:00:00-04:00",
                                          "2026-10-31T16:00:00-04:00",
                                          workspace_id=family["id"]))
    assert [c["title"] for c in store.list_commitments(university["id"])] == ["Exam"]
    assert [c["title"] for c in store.list_commitments(family["id"])] == ["School pickup"]
    assert len(store.list_commitments()) == 2, "an unscoped read still sees both"


def test_deleting_a_workspace_removes_its_commitments_only(store):
    keep = store.add_workspace(make_workspace("Keep", "Personal"))
    drop = store.add_workspace(make_workspace("Drop", "Gaming"))
    store.save_commitment(make_commitment("Stays", "2026-10-30T10:00:00-04:00",
                                          "2026-10-30T11:00:00-04:00",
                                          workspace_id=keep["id"]))
    store.save_commitment(make_commitment("Goes", "2026-10-30T12:00:00-04:00",
                                          "2026-10-30T13:00:00-04:00",
                                          workspace_id=drop["id"]))
    store.delete_workspace(drop["id"])
    assert [w["name"] for w in store.list_workspaces()] == ["Keep"]
    assert [c["title"] for c in store.list_commitments()] == ["Stays"]


def test_workspace_alias_can_be_updated_and_blanked(store):
    ws = store.add_workspace(make_workspace("Research", "Research", "Lab"))
    store.update_workspace(ws["id"], assistant_alias="")
    assert store.list_workspaces()[0]["assistant_alias"] == ""
    store.update_workspace(ws["id"], name="PhD Lab")
    assert store.list_workspaces()[0]["name"] == "PhD Lab"


def test_update_workspace_ignores_unknown_columns(store):
    ws = store.add_workspace(make_workspace("X", "Personal"))
    store.update_workspace(ws["id"], nonexistent="value")
    assert store.list_workspaces()[0]["name"] == "X"


# ----------------------------------------------------------- preferences
def test_preferences_fall_back_to_defaults(store):
    prefs = store.get_preferences()
    assert prefs["planning_buffer"] == 45
    assert prefs["assistant_alias"] == "Navi"


def test_preferences_round_trip_non_string_values(store):
    store.set_preferences({"planning_buffer": 90, "favorite_teams": ["A", "B"],
                           "share_schedule_with_ai": False})
    prefs = store.get_preferences()
    assert prefs["planning_buffer"] == 90
    assert prefs["favorite_teams"] == ["A", "B"]
    assert prefs["share_schedule_with_ai"] is False


def test_reset_restores_defaults(store):
    store.set_preference("planning_buffer", 5)
    store.reset_preferences()
    assert store.get_preferences()["planning_buffer"] == 45


# ------------------------------------------------- approval lifecycle (T13-T15)
def test_rejected_action_leaves_the_calendar_untouched(store, workspace):
    action = make_action("ADD_LOCAL_EVENT", "Volleyball", {}, "User asked")
    assert action["status"] == ACTION_PROPOSED
    action["status"] = ACTION_REJECTED
    action["result"] = "User rejected the proposal."
    store.save_action(action)
    assert store.list_commitments(workspace["id"]) == []
    assert store.list_actions()[0]["status"] == ACTION_REJECTED


def test_approved_action_inserts_once_and_verifies(store, workspace):
    record = make_commitment("Volleyball vs Milwaukee", "2026-10-30T18:00:00-04:00",
                             "2026-10-30T20:00:00-04:00", workspace_id=workspace["id"],
                             end_is_estimated=True)
    store.save_commitment(record)
    verified = store.commitment_exists(record["id"])
    action = make_action("ADD_LOCAL_EVENT", record["title"], {"id": record["id"]}, "Fits")
    action.update(status=ACTION_VERIFIED if verified else "FAILED", verified=verified)
    store.save_action(action)
    assert verified is True
    assert len(store.list_commitments(workspace["id"])) == 1
    assert store.list_actions()[0]["verified"] is True


def test_repeating_the_same_approval_creates_no_duplicate(store, workspace):
    title, start, end = "Volleyball", "2026-10-30T18:00:00-04:00", "2026-10-30T20:00:00-04:00"
    for _ in range(3):
        if store.find_duplicate(title, start, workspace["id"]):
            continue
        store.save_commitment(make_commitment(title, start, end,
                                              workspace_id=workspace["id"]))
    assert len(store.list_commitments(workspace["id"])) == 1


def test_action_history_is_newest_first(store):
    for index in range(3):
        action = make_action("ADD_LOCAL_EVENT", f"Event {index}", {}, "test")
        action["requested_at"] = f"2026-10-3{index}T10:00:00-04:00"
        store.save_action(action)
    assert [a["summary"] for a in store.list_actions()] == ["Event 2", "Event 1", "Event 0"]


# --------------------------------------------------------- notifications
def test_notification_deduplication(store):
    first = make_notification("weather", "Winter Storm Warning", "Overlaps exam",
                              related_id="exam:Winter Storm Warning")
    store.save_notification(first)
    assert store.notification_exists("weather", "exam:Winter Storm Warning")
    assert not store.notification_exists("weather", "exam:Other")
    assert not store.notification_exists("conflict", "exam:Winter Storm Warning")


def test_dismiss_marks_a_notification_without_deleting_it(store):
    notification = make_notification("conflict", "Overlap", "A overlaps B")
    store.save_notification(notification)
    store.dismiss_notification(notification["id"])
    stored = store.list_notifications()
    assert len(stored) == 1
    assert stored[0]["status"] == "dismissed"


# -------------------------------------------------------- export and erase
def test_export_contains_every_section_and_is_json_serialisable(store, workspace):
    store.save_commitment(make_commitment("Exam", "2026-10-31T09:00:00-04:00",
                                          "2026-10-31T10:30:00-04:00",
                                          workspace_id=workspace["id"]))
    store.save_action(make_action("ADD_LOCAL_EVENT", "Exam", {}, "test"))
    store.save_notification(make_notification("conflict", "T", "B"))
    store.set_preference("planning_buffer", 60)
    snapshot = store.export_all()
    assert set(snapshot) == {"exported_at", "note", "preferences", "workspaces",
                             "commitments", "actions", "notifications"}
    assert json.loads(json.dumps(snapshot))["preferences"]["planning_buffer"] == 60


def test_erase_all_clears_every_table(store, workspace):
    store.save_commitment(make_commitment("Exam", "2026-10-31T09:00:00-04:00",
                                          "2026-10-31T10:30:00-04:00",
                                          workspace_id=workspace["id"]))
    store.save_action(make_action("ADD_LOCAL_EVENT", "Exam", {}, "test"))
    store.save_notification(make_notification("conflict", "T", "B"))
    store.set_preference("planning_buffer", 60)
    store.erase_all()
    assert store.list_commitments() == []
    assert store.list_actions() == []
    assert store.list_notifications() == []
    assert store.list_workspaces() == []
    assert store.get_preferences()["planning_buffer"] == 45


# ------------------------------------------------------------- iCalendar
def test_ics_export_round_trips_through_the_parser():
    """Export then re-import must preserve the instant and the Michigan wall clock."""
    from kin_core import parse_dt
    original = [make_commitment("Organic chemistry", "2026-10-30T10:00:00-04:00",
                                "2026-10-30T11:30:00-04:00", event_type="class")]
    parsed = kin_calendar.parse_ics(kin_calendar.export_ics(original))
    assert len(parsed["events"]) == 1
    restored = parsed["events"][0]
    assert restored["title"] == "Organic chemistry"
    assert parse_dt(restored["start"]) == parse_dt(original[0]["start"])
    assert parse_dt(restored["end"]) == parse_dt(original[0]["end"])
    # Imported times are normalised to Michigan local, not left in UTC.
    assert restored["start"].startswith("2026-10-30T10:00")
    assert restored["start"].endswith("-04:00")


def test_ics_export_is_well_formed():
    text = kin_calendar.export_ics([make_commitment(
        "Exam", "2026-10-31T09:00:00-04:00", "2026-10-31T10:30:00-04:00")])
    assert text.startswith("BEGIN:VCALENDAR")
    assert text.rstrip().endswith("END:VCALENDAR")
    assert "VERSION:2.0" in text
    assert text.count("BEGIN:VEVENT") == text.count("END:VEVENT") == 1


def test_ics_export_notes_an_estimated_end_time():
    text = kin_calendar.export_ics([make_commitment(
        "Game", "2026-10-30T18:00:00-04:00", "2026-10-30T20:00:00-04:00",
        end_is_estimated=True)])
    assert "planning estimate" in text


def test_ics_import_handles_utc_tzid_and_all_day():
    raw = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
        "BEGIN:VEVENT\r\nUID:1\r\nSUMMARY:UTC meeting\r\n"
        "DTSTART:20261030T140000Z\r\nDTEND:20261030T150000Z\r\nEND:VEVENT\r\n"
        "BEGIN:VEVENT\r\nUID:2\r\nSUMMARY:Local class\r\n"
        "DTSTART;TZID=America/Detroit:20261030T100000\r\n"
        "DTEND;TZID=America/Detroit:20261030T113000\r\nEND:VEVENT\r\n"
        "BEGIN:VEVENT\r\nUID:3\r\nSUMMARY:Reading day\r\n"
        "DTSTART;VALUE=DATE:20261101\r\nEND:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    parsed = kin_calendar.parse_ics(raw)
    titles = [e["title"] for e in parsed["events"]]
    assert titles == ["UTC meeting", "Local class", "Reading day"]
    all_day = next(e for e in parsed["events"] if e["title"] == "Reading day")
    assert all_day["all_day"] is True


def test_ics_import_removes_duplicates_and_reports_them():
    event = ("BEGIN:VEVENT\r\nUID:{uid}\r\nSUMMARY:Lecture\r\n"
             "DTSTART:20261030T140000Z\r\nDTEND:20261030T150000Z\r\nEND:VEVENT\r\n")
    raw = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
           + event.format(uid="a") + event.format(uid="b") + "END:VCALENDAR\r\n")
    parsed = kin_calendar.parse_ics(raw)
    assert len(parsed["events"]) == 1
    assert parsed["duplicates_removed"] == 1


def test_ics_import_reports_skipped_and_invalid_rows():
    raw = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
        "BEGIN:VEVENT\r\nUID:1\r\nSUMMARY:No start\r\nEND:VEVENT\r\n"
        "BEGIN:VEVENT\r\nUID:2\r\nSUMMARY:Backwards\r\n"
        "DTSTART:20261030T150000Z\r\nDTEND:20261030T140000Z\r\nEND:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    parsed = kin_calendar.parse_ics(raw)
    assert parsed["events"] == []
    assert len(parsed["skipped"]) == 2


def test_ics_import_flags_recurring_events_instead_of_expanding_them():
    raw = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:1\r\n"
           "SUMMARY:Weekly lab\r\nDTSTART:20261030T140000Z\r\nDTEND:20261030T150000Z\r\n"
           "RRULE:FREQ=WEEKLY;COUNT=10\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
    parsed = kin_calendar.parse_ics(raw)
    assert len(parsed["events"]) == 1
    assert parsed["recurring_first_occurrence_only"] == 1


def test_ics_import_uses_duration_when_dtend_is_absent():
    raw = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:1\r\n"
           "SUMMARY:Timed by duration\r\nDTSTART:20261030T140000Z\r\n"
           "DURATION:PT1H30M\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
    event = kin_calendar.parse_ics(raw)["events"][0]
    from kin_core import parse_dt
    assert (parse_dt(event["end"]) - parse_dt(event["start"])).total_seconds() == 5400


def test_ics_import_marks_cancelled_status():
    raw = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:1\r\n"
           "SUMMARY:Called off\r\nDTSTART:20261030T140000Z\r\nDTEND:20261030T150000Z\r\n"
           "STATUS:CANCELLED\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n")
    assert kin_calendar.parse_ics(raw)["events"][0]["status"] == "canceled"


def test_ics_import_unfolds_long_folded_lines():
    long_title = "A very long lecture title that will certainly exceed the folding limit"
    raw = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:1\r\n"
           f"SUMMARY:{long_title[:40]}\r\n {long_title[40:]}\r\n"
           "DTSTART:20261030T140000Z\r\nDTEND:20261030T150000Z\r\nEND:VEVENT\r\n"
           "END:VCALENDAR\r\n")
    assert kin_calendar.parse_ics(raw)["events"][0]["title"] == long_title


def test_ics_import_is_safe_on_garbage_input():
    parsed = kin_calendar.parse_ics("this is not a calendar file at all")
    assert parsed["events"] == []
    assert parsed["skipped"] == []
