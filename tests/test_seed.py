"""Tests for the fictional life-dataset loader.

The dataset is authored in local wall-clock time, so the loader is the component
responsible for attaching the correct America/Detroit offset on each side of the
1 November 2026 daylight-saving change. That is what most of these tests check.
"""
import importlib
import json

import pytest

import kin_seed
import kin_store
from kin_core import detect_internal_conflicts
from kin_seed import SeedError, load_file, parse_dataset

MINIMAL = {
    "profile": {"preferred_name": "Mira", "planning_buffer": 50},
    "workspaces": [{"name": "OU", "kind": "University", "assistant_alias": "Grizz"}],
    "recurring": [],
    "one_off": [{"workspace": "OU", "title": "Midterm", "event_type": "exam",
                 "requires_travel": True, "start": "2026-10-21T09:00",
                 "end": "2026-10-21T10:30", "status": "completed", "notes": "n"}],
}


@pytest.fixture()
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("KIN_DB_PATH", str(tmp_path / "seed.db"))
    module = importlib.reload(kin_store)
    module.init_db()
    return module


# ------------------------------------------------------- daylight saving
def test_october_times_get_edt_and_december_gets_est():
    data = dict(MINIMAL, one_off=[
        {"workspace": "OU", "title": "October exam", "event_type": "exam",
         "requires_travel": True, "start": "2026-10-21T09:00", "end": "2026-10-21T10:30"},
        {"workspace": "OU", "title": "December final", "event_type": "exam",
         "requires_travel": True, "start": "2026-12-07T09:00", "end": "2026-12-07T11:00"},
    ])
    by_title = {c["title"]: c for c in parse_dataset(data)["commitments"]}
    assert by_title["October exam"]["start"].endswith("-04:00")
    assert by_title["December final"]["start"].endswith("-05:00")


def test_a_recurring_pattern_switches_offset_across_the_dst_boundary():
    """One weekly pattern spanning 1 November must emit both offsets."""
    data = dict(MINIMAL, recurring=[{
        "workspace": "OU", "title": "Weekly lecture", "event_type": "class",
        "requires_travel": True, "days": ["MO"], "start_time": "09:00",
        "end_time": "10:07", "from_date": "2026-10-26", "to_date": "2026-11-09",
    }], one_off=[])
    events = parse_dataset(data)["commitments"]
    offsets = {c["start"][:10]: c["start"][-6:] for c in events}
    assert offsets["2026-10-26"] == "-04:00"
    assert offsets["2026-11-02"] == "-05:00"
    assert offsets["2026-11-09"] == "-05:00"
    # The wall-clock time the student sees never drifts.
    assert all(c["start"][11:16] == "09:00" for c in events)


def test_an_offset_supplied_in_the_file_is_rederived_and_reported():
    data = dict(MINIMAL, one_off=[
        {"workspace": "OU", "title": "Wrongly offset", "event_type": "exam",
         "requires_travel": True, "start": "2026-10-21T09:00:00-05:00",
         "end": "2026-10-21T10:30:00-05:00"}])
    parsed = parse_dataset(data)
    assert any("already carried an offset" in p for p in parsed["problems"])
    # 09:00 EST is 10:00 EDT; the instant is preserved rather than silently shifted.
    assert parsed["commitments"][0]["start"] == "2026-10-21T10:00:00-04:00"


# ------------------------------------------------------- recurring expansion
def test_recurring_pattern_expands_onto_the_right_weekdays():
    data = dict(MINIMAL, recurring=[{
        "workspace": "OU", "title": "MWF class", "event_type": "class",
        "requires_travel": True, "days": ["MO", "WE", "FR"],
        "start_time": "09:00", "end_time": "10:07",
        "from_date": "2026-09-07", "to_date": "2026-09-18",
    }], one_off=[])
    events = [c for c in parse_dataset(data)["commitments"] if c["title"] == "MWF class"]
    assert len(events) == 6
    from kin_core import parse_dt
    assert {parse_dt(c["start"]).weekday() for c in events} == {0, 2, 4}


def test_past_recurring_instances_are_completed_and_future_are_planned():
    data = dict(MINIMAL, recurring=[{
        "workspace": "OU", "title": "Spanning class", "event_type": "class",
        "requires_travel": True, "days": ["MO"], "start_time": "09:00",
        "end_time": "10:07", "from_date": "2026-10-19", "to_date": "2026-11-09",
    }], one_off=[])
    events = {c["start"][:10]: c["status"] for c in parse_dataset(data)["commitments"]}
    assert events["2026-10-19"] == "completed"
    assert events["2026-10-26"] == "completed"
    assert events["2026-11-02"] == "planned"


def test_recurring_instances_are_tagged_with_their_origin():
    data = dict(MINIMAL, recurring=[{
        "workspace": "OU", "title": "C", "event_type": "class", "requires_travel": True,
        "days": ["MO"], "start_time": "09:00", "end_time": "10:00",
        "from_date": "2026-11-02", "to_date": "2026-11-02"}], one_off=[])
    assert parse_dataset(data)["commitments"][0]["origin"] == "seed:recurring"


# --------------------------------------------------------- bad input handling
def test_unknown_event_type_is_reported_not_silently_accepted():
    data = dict(MINIMAL, one_off=[
        {"workspace": "OU", "title": "Odd", "event_type": "telepathy",
         "requires_travel": True, "start": "2026-11-02T09:00", "end": "2026-11-02T10:00"}])
    parsed = parse_dataset(data)
    assert parsed["commitments"][0]["event_type"] == "personal"
    assert any("telepathy" in p for p in parsed["problems"])


def test_unknown_workspace_is_reported_and_reassigned():
    data = dict(MINIMAL, one_off=[
        {"workspace": "Does Not Exist", "title": "Orphan", "event_type": "class",
         "requires_travel": True, "start": "2026-11-02T09:00", "end": "2026-11-02T10:00"}])
    parsed = parse_dataset(data)
    assert any("unknown workspace" in p for p in parsed["problems"])
    assert parsed["commitments"][0]["workspace_id"] == parsed["workspaces"][0]["id"]


def test_reversed_and_overlong_events_are_skipped_with_a_reason():
    data = dict(MINIMAL, one_off=[
        {"workspace": "OU", "title": "Backwards", "event_type": "class",
         "requires_travel": True, "start": "2026-11-02T10:00", "end": "2026-11-02T09:00"},
        {"workspace": "OU", "title": "Endless", "event_type": "class",
         "requires_travel": True, "start": "2026-11-02T09:00", "end": "2026-11-09T09:00"},
        {"workspace": "OU", "title": "Fine", "event_type": "class",
         "requires_travel": True, "start": "2026-11-02T09:00", "end": "2026-11-02T10:00"},
    ])
    parsed = parse_dataset(data)
    assert [c["title"] for c in parsed["commitments"]] == ["Fine"]
    assert len(parsed["problems"]) == 2


def test_pattern_with_no_valid_weekday_is_skipped():
    data = dict(MINIMAL, recurring=[{
        "workspace": "OU", "title": "Nowhere", "event_type": "class",
        "requires_travel": True, "days": ["XX"], "start_time": "09:00",
        "end_time": "10:00", "from_date": "2026-11-02", "to_date": "2026-11-30"}])
    parsed = parse_dataset(data)
    assert not any(c["title"] == "Nowhere" for c in parsed["commitments"])
    assert any("weekday" in p for p in parsed["problems"])


def test_duplicate_rows_are_collapsed():
    duplicate = {"workspace": "OU", "title": "Same", "event_type": "class",
                 "requires_travel": True, "start": "2026-11-02T09:00",
                 "end": "2026-11-02T10:00"}
    parsed = parse_dataset(dict(MINIMAL, one_off=[duplicate, dict(duplicate)]))
    assert len([c for c in parsed["commitments"] if c["title"] == "Same"]) == 1


@pytest.mark.parametrize("bad", [
    "not a dict", {}, {"profile": {}}, {"workspaces": []},
    {"profile": {}, "workspaces": [{"kind": "University"}]},
    {"profile": {}, "workspaces": [{"name": "OU", "kind": "University"}]},
])
def test_structurally_unusable_files_raise(bad):
    with pytest.raises(SeedError):
        parse_dataset(bad)


def test_missing_file_raises_rather_than_returning_empty(tmp_path):
    with pytest.raises(SeedError, match="No dataset file"):
        kin_seed.load_file(tmp_path / "absent.json")


def test_invalid_json_raises_with_context(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(SeedError, match="not valid JSON"):
        kin_seed.load_file(path)


# ------------------------------------------------------------------ install
def test_install_replaces_existing_data_and_applies_preferences(store):
    from kin_models import make_commitment, make_workspace
    old = store.add_workspace(make_workspace("Old", "Personal"))
    store.save_commitment(make_commitment("Leftover", "2026-10-01T09:00:00-04:00",
                                          "2026-10-01T10:00:00-04:00",
                                          workspace_id=old["id"]))
    report = kin_seed.install(store, parse_dataset(MINIMAL))
    assert report["commitments"] == 1
    assert [w["name"] for w in store.list_workspaces()] == ["OU"]
    assert [c["title"] for c in store.list_commitments()] == ["Midterm"]
    assert store.get_preferences()["planning_buffer"] == 50
    assert store.get_preferences()["preferred_name"] == "Mira"


def test_install_twice_does_not_duplicate(store):
    kin_seed.install(store, parse_dataset(MINIMAL))
    kin_seed.install(store, parse_dataset(MINIMAL))
    assert len(store.list_commitments()) == 1
    assert len(store.list_workspaces()) == 1


def test_workspace_alias_null_is_preserved_as_inherit(store):
    data = dict(MINIMAL, workspaces=[
        {"name": "OU", "kind": "University", "assistant_alias": "Grizz"},
        {"name": "Lab", "kind": "Research", "assistant_alias": None}])
    kin_seed.install(store, parse_dataset(data))
    aliases = {w["name"]: w["assistant_alias"] for w in store.list_workspaces()}
    assert aliases["OU"] == "Grizz"
    assert aliases["Lab"] is None


# ----------------------------------------------- the real shipped dataset
@pytest.mark.skipif(not kin_seed.dataset_available(),
                    reason="the fictional dataset file is not present")
class TestShippedDataset:
    def test_it_parses_with_no_problems(self):
        parsed = load_file()
        assert parsed["problems"] == [], parsed["problems"]
        assert len(parsed["commitments"]) > 250
        assert len(parsed["workspaces"]) >= 5

    def test_every_offset_is_correct_for_its_date(self):
        """No row may carry an offset that America/Detroit does not use that day."""
        from kin_core import michigan_offset_matches
        for c in load_file()["commitments"]:
            assert michigan_offset_matches(c["start"]), c
            assert michigan_offset_matches(c["end"]), c

    def test_it_spans_the_dst_change_in_both_directions(self):
        offsets = {c["start"][-6:] for c in load_file()["commitments"]}
        assert offsets == {"-04:00", "-05:00"}

    def test_it_contains_both_history_and_december_planning(self):
        starts = [c["start"][:7] for c in load_file()["commitments"]]
        assert "2026-08" in starts
        assert "2026-12" in starts

    def test_past_events_are_completed_and_future_are_not(self):
        for c in load_file()["commitments"]:
            if c["start"] < "2026-10-29":
                assert c["status"] in ("completed", "canceled"), c["title"]

    def test_it_produces_detectable_upcoming_clashes(self):
        """The dataset's deliberate conflicts must reach the Ripple Engine."""
        conflicts = detect_internal_conflicts(load_file()["commitments"])
        assert len(conflicts) >= 3

    def test_it_is_explicitly_fictional(self):
        profile = load_file()["profile"]
        assert "fictional" in profile.get("backstory", "").lower()

    def test_it_loads_into_a_store_quickly_enough_for_the_ui(self, store):
        import time
        parsed = load_file()
        started = time.perf_counter()
        kin_seed.install(store, parsed)
        assert time.perf_counter() - started < 10
        assert len(store.list_commitments()) == len(parsed["commitments"])

    def test_conflict_detection_stays_fast_at_full_dataset_size(self, store):
        import time
        kin_seed.install(store, load_file())
        everything = store.list_commitments()
        started = time.perf_counter()
        detect_internal_conflicts(everything)
        elapsed = time.perf_counter() - started
        assert elapsed < 1.0, f"{len(everything)} commitments took {elapsed:.2f}s"
