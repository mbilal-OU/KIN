"""Deterministic rule tests. No network, no model calls, no clock dependence."""
import pytest

from kin_core import (
    assess_alerts, assess_opportunities, detect_internal_conflicts, effective_window,
    find_free_windows, michigan_offset_matches, overlaps, sample_commitments,
    simulate_change, simulated_alert, validate_event_proposal,
)
from kin_models import michigan_offset_for

from datetime import datetime
from zoneinfo import ZoneInfo

MICHIGAN = ZoneInfo("America/Detroit")


# ------------------------------------------------- original starter tests (T01-T03)
def test_overlap_positive():
    assert overlaps("2026-10-31T08:00:00-04:00", "2026-10-31T09:00:00-04:00", "2026-10-31T08:30:00-04:00", "2026-10-31T10:00:00-04:00")


def test_touching_events_are_not_conflicts():
    assert not overlaps("2026-10-31T08:00:00-04:00", "2026-10-31T09:00:00-04:00", "2026-10-31T09:00:00-04:00", "2026-10-31T10:00:00-04:00")


def test_simulated_alert_hits_exam():
    alerts = assess_alerts(sample_commitments(), [simulated_alert()], commute_minutes=45)
    assert len(alerts) == 1
    assert alerts[0]["event_id"] == "exam"
    assert alerts[0]["is_simulation"]
    assert "no university cancellation" in alerts[0]["status"]


def test_opportunity_conflict_and_free_slot():
    commitments = [{"id": "1", "title": "Lab", "start": "2026-10-30T17:30:00-04:00", "end": "2026-10-30T18:30:00-04:00"}]
    options = [{"id": "game", "title": "Game", "start": "2026-10-30T18:00:00-04:00", "end": "2026-10-30T20:00:00-04:00"}, {"id": "later", "title": "Later", "start": "2026-10-31T18:00:00-04:00", "end": "2026-10-31T20:00:00-04:00"}]
    results = assess_opportunities(commitments, options)
    assert not results[0]["fits"]
    assert results[1]["fits"]


def test_model_proposal_validation():
    valid = {"title": "Biology Study", "start": "2026-10-30T17:00:00-04:00", "end": "2026-10-30T17:45:00-04:00", "requires_travel": True}
    assert validate_event_proposal(valid)["title"] == "Biology Study"


def test_model_proposal_rejects_unzoned_dates():
    with pytest.raises(ValueError):
        validate_event_proposal({"title": "Exam", "start": "2026-10-30T17:00:00", "end": "2026-10-30T18:00:00", "requires_travel": True})


# ------------------------------------------------------- daylight saving (T04)
def test_michigan_offset_differs_across_dst_boundary():
    assert michigan_offset_for(datetime(2026, 10, 30, 9, 0)) == "-04:00"
    assert michigan_offset_for(datetime(2026, 11, 15, 9, 0)) == "-05:00"


def test_strict_validation_rejects_wrong_dst_offset():
    """A model emitting EST for an EDT date must be caught, not silently stored."""
    wrong = {"title": "Exam", "start": "2026-10-30T09:00:00-05:00",
             "end": "2026-10-30T10:00:00-05:00", "requires_travel": True}
    with pytest.raises(ValueError, match="America/Detroit"):
        validate_event_proposal(wrong, strict_michigan=True)
    # Without the strict flag the already-working path is unchanged.
    assert validate_event_proposal(wrong)["title"] == "Exam"


def test_strict_validation_accepts_correct_offsets_either_side_of_dst():
    for start, end in [("2026-10-30T09:00:00-04:00", "2026-10-30T10:00:00-04:00"),
                       ("2026-11-15T09:00:00-05:00", "2026-11-15T10:00:00-05:00")]:
        assert validate_event_proposal(
            {"title": "Class", "start": start, "end": end, "requires_travel": True},
            strict_michigan=True)


def test_utc_expressed_instant_is_accepted():
    """09:00 EDT written as 13:00Z is the same instant and must not be rejected."""
    assert michigan_offset_matches("2026-10-30T13:00:00+00:00")


# --------------------------------------------------- buffers and travel (T06)
def test_remote_commitment_gets_no_travel_buffer():
    remote = [{"id": "remote", "title": "Remote standup", "requires_travel": False,
               "start": "2026-10-31T07:00:00-04:00", "end": "2026-10-31T07:30:00-04:00"}]
    # The simulated warning starts 06:30; a 60-minute buffer would reach back to
    # 06:00 and overlap, but a remote meeting must not get a travel buffer.
    assert assess_alerts(remote, [simulated_alert()], commute_minutes=60) != []
    early = [{"id": "remote2", "title": "Remote call", "requires_travel": False,
              "start": "2026-10-31T06:00:00-04:00", "end": "2026-10-31T06:25:00-04:00"}]
    assert assess_alerts(early, [simulated_alert()], commute_minutes=60) == []


def test_buffer_pulls_commitment_into_alert_window():
    late = [{"id": "late", "title": "Noon class", "requires_travel": True,
             "start": "2026-10-31T12:30:00-04:00", "end": "2026-10-31T13:30:00-04:00"}]
    assert assess_alerts(late, [simulated_alert()], commute_minutes=0) == []
    assert len(assess_alerts(late, [simulated_alert()], commute_minutes=45)) == 1


def test_effective_window_rejects_absurd_buffer():
    with pytest.raises(ValueError):
        effective_window(sample_commitments()[0], 999)


# ------------------------------------------------- alert handling edge cases
def test_alert_without_times_is_ignored_not_guessed():
    nameless = [{"event": "Flood Watch", "severity": "Moderate"}]
    assert assess_alerts(sample_commitments(), nameless, 45) == []


def test_reissued_alert_yields_one_impact_at_highest_severity():
    minor = {**simulated_alert(), "severity": "Minor"}
    extreme = {**simulated_alert(), "severity": "Extreme"}
    impacts = assess_alerts(sample_commitments(), [minor, extreme], 45)
    assert len(impacts) == 1
    assert impacts[0]["severity"] == "Extreme"


def test_canceled_commitment_is_not_assessed():
    canceled = [dict(c, status="canceled") for c in sample_commitments()]
    assert assess_alerts(canceled, [simulated_alert()], 45) == []


def test_simulation_flag_survives_assessment():
    """A simulated alert must never be reported as official NWS data."""
    live = {"event": "Winter Weather Advisory", "severity": "Moderate",
            "onset": "2026-10-31T06:30:00-04:00", "ends": "2026-10-31T12:00:00-04:00",
            "source_url": "https://api.weather.gov/alerts/x", "is_simulation": False}
    impacts = assess_alerts(sample_commitments(), [live, simulated_alert()], 45)
    flags = {i["alert"]: i["is_simulation"] for i in impacts}
    assert flags["Winter Weather Advisory"] is False
    assert flags["SIMULATED Winter Storm Warning"] is True


# ----------------------------------------------------- opportunities (T16)
def test_estimated_end_time_is_reported_as_such():
    option = [{"id": "g", "title": "Game", "start": "2026-11-05T18:00:00-05:00",
               "end": "2026-11-05T20:00:00-05:00", "end_is_estimated": True}]
    assert assess_opportunities([], option)[0]["certainty"] == "estimated_end"


def test_completed_commitment_does_not_block_an_opportunity():
    done = [{"id": "d", "title": "Finished lab", "status": "completed",
             "start": "2026-10-30T18:00:00-04:00", "end": "2026-10-30T19:00:00-04:00"}]
    option = [{"id": "g", "title": "Game", "start": "2026-10-30T18:00:00-04:00",
               "end": "2026-10-30T20:00:00-04:00"}]
    assert assess_opportunities(done, option)[0]["fits"]


def test_buffer_size_changes_the_verdict():
    commitments = [{"id": "c", "title": "Class", "start": "2026-10-30T17:00:00-04:00",
                    "end": "2026-10-30T17:45:00-04:00"}]
    option = [{"id": "g", "title": "Game", "start": "2026-10-30T18:00:00-04:00",
               "end": "2026-10-30T20:00:00-04:00"}]
    assert assess_opportunities(commitments, option, buffer_minutes=0)[0]["fits"]
    assert not assess_opportunities(commitments, option, buffer_minutes=30)[0]["fits"]


# ------------------------------------------------- internal conflicts & free time
def test_detect_internal_conflicts_finds_one_pair():
    overlapping = [
        {"id": "a", "title": "Lecture", "start": "2026-10-30T10:00:00-04:00",
         "end": "2026-10-30T11:30:00-04:00"},
        {"id": "b", "title": "Lab", "start": "2026-10-30T11:00:00-04:00",
         "end": "2026-10-30T12:00:00-04:00"},
        {"id": "c", "title": "Later", "start": "2026-10-30T15:00:00-04:00",
         "end": "2026-10-30T16:00:00-04:00"},
    ]
    found = detect_internal_conflicts(overlapping)
    assert len(found) == 1
    assert {found[0]["a"], found[0]["b"]} == {"Lecture", "Lab"}


def test_free_windows_respect_minimum_length():
    day = datetime(2026, 10, 30, tzinfo=MICHIGAN)
    busy = [{"id": "x", "title": "Long class", "start": "2026-10-30T08:00:00-04:00",
             "end": "2026-10-30T21:30:00-04:00"}]
    assert find_free_windows(busy, day, minimum_minutes=45) == []
    windows = find_free_windows([], day, minimum_minutes=45)
    assert len(windows) == 1


# --------------------------------------------------------- what-if simulator
def test_simulator_reports_new_conflict_without_mutating_input():
    commitments = [
        {"id": "exam", "title": "Exam", "start": "2026-10-31T09:00:00-04:00",
         "end": "2026-10-31T10:30:00-04:00"},
        {"id": "shift", "title": "Work shift", "start": "2026-10-31T11:00:00-04:00",
         "end": "2026-10-31T15:00:00-04:00"},
    ]
    snapshot = [dict(c) for c in commitments]
    result = simulate_change(commitments, move_id="shift", shift_minutes=-90)
    assert result["net_change"] == 1
    assert len(result["new_conflicts"]) == 1
    assert result["applied"] is False
    assert commitments == snapshot, "simulate_change must not mutate the timetable"


def test_simulator_reports_resolved_conflict():
    clashing = [
        {"id": "a", "title": "A", "start": "2026-10-30T10:00:00-04:00",
         "end": "2026-10-30T11:30:00-04:00"},
        {"id": "b", "title": "B", "start": "2026-10-30T11:00:00-04:00",
         "end": "2026-10-30T12:00:00-04:00"},
    ]
    result = simulate_change(clashing, move_id="b", shift_minutes=120)
    assert len(result["resolved_conflicts"]) == 1
    assert result["net_change"] == -1
