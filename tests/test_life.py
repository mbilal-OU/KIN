"""Tests for KIN's free-first manual life planner. No API or network calls."""
from copy import deepcopy
from datetime import date, datetime, time, timezone

import pytest

from kin_life import (
    build_manual_occurrences, default_scheduling_mode, suggest_alternative_slots,
)
from kin_models import make_commitment


def make_event(name, start, end, *, mode="fixed", travel=False, status="planned"):
    item = make_commitment(name, start, end, event_type="personal",
                           requires_travel=travel, status=status)
    item["scheduling_mode"] = mode
    return item


def test_fixed_is_default_for_university_and_work():
    assert default_scheduling_mode("class") == "fixed"
    assert default_scheduling_mode("work") == "fixed"
    assert default_scheduling_mode("exam") == "fixed"
    assert default_scheduling_mode("study") == "flexible"


def test_single_manual_record_has_no_fake_recurrence():
    result = build_manual_occurrences(
        "Lab", date(2026, 11, 3), time(10), time(11),
        event_type="lab", scheduling_mode="fixed")
    assert len(result) == 1
    assert result[0]["origin"] == "manual"
    assert result[0]["scheduling_mode"] == "fixed"
    assert "series_id" not in result[0]


def test_weekdays_expand_to_five_distinct_rows_and_preserve_dst():
    records = build_manual_occurrences(
        "Study", date(2026, 10, 30), time(9), time(10),
        scheduling_mode="flexible", repeat="Weekdays", weeks=1)
    assert len(records) == 5
    assert records[0]["start"].endswith("-04:00")
    assert all(x["start"].endswith("-05:00") for x in records[1:])
    assert len({x["id"] for x in records}) == 5
    assert len({x["series_id"] for x in records}) == 1
    assert {x["repeat_rule"] for x in records} == {"Weekdays"}


def test_weekly_repeat_keeps_local_clock_time_across_dst():
    records = build_manual_occurrences(
        "Gym", date(2026, 10, 26), time(18), time(19),
        scheduling_mode="flexible", repeat="Every week", weeks=3)
    assert len(records) == 3
    assert all("T18:00:00" in x["start"] for x in records)
    assert records[0]["start"].endswith("-04:00")
    assert records[1]["start"].endswith("-05:00")


def test_daily_repeat_is_bounded():
    records = build_manual_occurrences(
        "Read", date(2026, 11, 3), time(20), time(21),
        repeat="Every day", weeks=12)
    assert len(records) == 84
    with pytest.raises(ValueError, match="1 and 12"):
        build_manual_occurrences("Read", date(2026, 11, 3), time(20), time(21),
                                 repeat="Every day", weeks=13)


def test_invalid_or_ambiguous_manual_times_refused():
    with pytest.raises(ValueError, match="End time"):
        build_manual_occurrences("Backward", date(2026, 11, 3), time(12), time(11))
    with pytest.raises(ValueError, match="does not exist"):
        build_manual_occurrences("Spring", date(2026, 3, 8), time(2, 30), time(3, 30))
    with pytest.raises(ValueError, match="ambiguous"):
        build_manual_occurrences("Autumn", date(2026, 11, 1), time(1, 30), time(2, 30))


def test_suggest_never_moves_fixed_or_protected_items():
    for mode in ("fixed", "protected"):
        only = make_event("Class", "2026-11-04T10:00:00-05:00",
                          "2026-11-04T11:00:00-05:00", mode=mode)
        assert suggest_alternative_slots([only], only["id"]) == []


def test_free_suggestions_are_conflict_free_and_inputs_unchanged():
    flexible = make_event("Gym", "2026-11-04T10:00:00-05:00",
                           "2026-11-04T11:00:00-05:00", mode="flexible")
    class_event = make_event("Class", "2026-11-04T10:30:00-05:00",
                             "2026-11-04T12:00:00-05:00")
    original = deepcopy([flexible, class_event])
    choices = suggest_alternative_slots([flexible, class_event], flexible["id"],
                                        earliest_hour=8, latest_hour=20)
    assert choices
    assert all(x["start"] != flexible["start"] for x in choices)
    from kin_core import overlaps
    assert all(not overlaps(x["start"], x["end"], class_event["start"],
                            class_event["end"]) for x in choices)
    assert [flexible, class_event] == original


def test_buffer_blocks_too_close_of_a_suggestion():
    flexible = make_event("Study", "2026-11-04T10:00:00-05:00",
                           "2026-11-04T11:00:00-05:00", mode="flexible", travel=True)
    fixed = make_event("Lab", "2026-11-04T11:00:00-05:00",
                       "2026-11-04T12:00:00-05:00")
    choices = suggest_alternative_slots(
        [flexible, fixed], flexible["id"], earliest_hour=8, latest_hour=16,
        buffer_minutes=30, days_ahead=1, max_results=20)
    assert choices
    assert all(not ("2026-11-04T12:00:00" <= c["start"] <
                    "2026-11-04T12:30:00") for c in choices)


def test_not_before_excludes_earlier_times():
    flexible = make_event("Study", "2026-11-04T09:00:00-05:00",
                           "2026-11-04T10:00:00-05:00", mode="flexible")
    cutoff = datetime(2026, 11, 4, 14, tzinfo=timezone.utc)
    choices = suggest_alternative_slots([flexible], flexible["id"],
                                        not_before=cutoff, days_ahead=1)
    assert choices
    assert all(datetime.fromisoformat(x["start"]).astimezone(timezone.utc) >= cutoff
               for x in choices)


def test_canceled_and_completed_items_do_not_block():
    flexible = make_event("Gym", "2026-11-04T09:00:00-05:00",
                           "2026-11-04T10:00:00-05:00", mode="flexible")
    old = make_event("Canceled", "2026-11-04T10:00:00-05:00",
                     "2026-11-04T11:00:00-05:00", status="canceled")
    result = suggest_alternative_slots([flexible, old], flexible["id"],
                                       earliest_hour=9, latest_hour=12, days_ahead=1)
    assert any(x["start"].startswith("2026-11-04T10:00:00") for x in result)


def test_unknown_target_and_naive_cutoff_rejected():
    with pytest.raises(ValueError, match="not found"):
        suggest_alternative_slots([], "missing")
    event = make_event("Gym", "2026-11-04T09:00:00-05:00",
                       "2026-11-04T10:00:00-05:00", mode="flexible")
    with pytest.raises(ValueError, match="timezone-aware"):
        suggest_alternative_slots([event], event["id"],
                                  not_before=datetime(2026, 11, 4, 10))


def test_proposals_do_not_claim_to_modify_authoritative_schedules():
    work = make_event("Employer shift", "2026-11-04T10:00:00-05:00",
                      "2026-11-04T12:00:00-05:00", mode="fixed")
    flexible = make_event("Reading", "2026-11-04T11:00:00-05:00",
                          "2026-11-04T12:00:00-05:00", mode="flexible")
    proposals = suggest_alternative_slots([work, flexible], flexible["id"])
    assert proposals
    assert work["start"] == "2026-11-04T10:00:00-05:00"
    assert flexible["start"] == "2026-11-04T11:00:00-05:00"
