"""Weather adapter tests. Every network call is mocked: no live NWS traffic.

The behaviour under test is the honesty contract from the plan: a failure says
"unavailable", never "no alerts", and one location's data can never be shown
under another location's name.
"""
import pytest
import requests

import kin_sources
from kin_core import assess_alerts, sample_commitments
from kin_sources import categorize_hazard, get_weather, weather_matches_location

POINT_RESPONSE = {"properties": {"cwa": "DTX",
                                 "forecastHourly": "https://api.weather.gov/x/hourly"}}
FORECAST_RESPONSE = {"properties": {"periods": [
    {"startTime": "2026-10-30T15:00:00-04:00", "temperature": 48,
     "temperatureUnit": "F", "shortForecast": "Cloudy"}]}}


def _alert_feature(**overrides):
    properties = {
        "event": "Winter Storm Warning", "severity": "Severe", "certainty": "Likely",
        "urgency": "Expected", "headline": "Heavy snow expected",
        "description": "Plan on difficult travel conditions.",
        "onset": "2026-10-31T06:30:00-04:00", "ends": "2026-10-31T12:00:00-04:00",
        "web": "https://api.weather.gov/alerts/abc",
    }
    properties.update(overrides)
    return {"id": "urn:oid:test", "properties": properties}


def _router(mapping):
    """Return a fake _get that dispatches on a URL substring."""
    def fake_get(url):
        for fragment, outcome in mapping.items():
            if fragment in url:
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome
        raise AssertionError(f"unexpected URL requested: {url}")
    return fake_get


# ----------------------------------------------------------- happy path (T07)
def test_successful_fetch_records_status_and_provenance(monkeypatch):
    monkeypatch.setattr(kin_sources, "_get", _router({
        "/points/": POINT_RESPONSE,
        "/hourly": FORECAST_RESPONSE,
        "/alerts/active": {"features": [_alert_feature()]},
    }))
    data = get_weather(42.672, -83.218, "Oakland University campus (approx.)")
    assert data["forecast_status"] == "retrieved"
    assert data["alerts_status"] == "retrieved"
    assert data["errors"] == []
    assert data["city"] == "Oakland University campus (approx.)"
    assert data["office"] == "DTX"
    assert data["alerts"][0]["is_simulation"] is False
    assert data["alerts"][0]["source_url"].startswith("https://")
    assert data["retrieved_at"]


def test_zero_alerts_is_a_retrieved_result_not_a_failure(monkeypatch):
    monkeypatch.setattr(kin_sources, "_get", _router({
        "/points/": POINT_RESPONSE,
        "/hourly": FORECAST_RESPONSE,
        "/alerts/active": {"features": []},
    }))
    data = get_weather(42.672, -83.218, "Troy (approx.)")
    assert data["alerts_status"] == "retrieved"
    assert data["alerts"] == []
    assert data["errors"] == []


# -------------------------------------------------------------- failures (T08)
def test_alert_timeout_reports_unavailable_and_never_implies_safety(monkeypatch):
    monkeypatch.setattr(kin_sources, "_get", _router({
        "/points/": POINT_RESPONSE,
        "/hourly": FORECAST_RESPONSE,
        "/alerts/active": requests.Timeout("timed out"),
    }))
    data = get_weather(42.672, -83.218, "Pontiac (approx.)")
    assert data["alerts_status"] == "unavailable"
    assert "timeout" in data["error_kinds"]
    joined = " ".join(data["errors"]).lower()
    assert "unavailable" in joined
    assert "no alerts" not in joined


def test_forecast_failure_leaves_alerts_working(monkeypatch):
    monkeypatch.setattr(kin_sources, "_get", _router({
        "/points/": requests.ConnectionError("dns"),
        "/alerts/active": {"features": [_alert_feature()]},
    }))
    data = get_weather(42.672, -83.218, "Troy (approx.)")
    assert data["forecast_status"] == "unavailable"
    assert data["alerts_status"] == "retrieved"
    assert "network" in data["error_kinds"]


def test_http_error_is_classified_with_its_status_code(monkeypatch):
    response = requests.Response()
    response.status_code = 503
    error = requests.HTTPError("service unavailable", response=response)
    monkeypatch.setattr(kin_sources, "_get", _router({
        "/points/": error, "/alerts/active": error,
    }))
    data = get_weather(42.672, -83.218, "Troy (approx.)")
    assert data["error_kinds"] == ["http_503", "http_503"]
    assert data["alerts_status"] == "unavailable"


def test_malformed_payload_does_not_crash(monkeypatch):
    monkeypatch.setattr(kin_sources, "_get", _router({
        "/points/": {"properties": {}},               # no forecastHourly key
        "/alerts/active": {"unexpected": "shape"},
    }))
    data = get_weather(42.672, -83.218, "Troy (approx.)")
    assert data["forecast_status"] == "unavailable"
    assert data["alerts_status"] == "retrieved"
    assert data["alerts"] == []


def test_alert_missing_both_end_fields_is_skipped_by_the_engine(monkeypatch):
    monkeypatch.setattr(kin_sources, "_get", _router({
        "/points/": POINT_RESPONSE, "/hourly": FORECAST_RESPONSE,
        "/alerts/active": {"features": [_alert_feature(ends=None, expires=None)]},
    }))
    data = get_weather(42.672, -83.218, "Troy (approx.)")
    assert data["alerts_status"] == "retrieved"
    assert assess_alerts(sample_commitments(), data["alerts"], 45) == []


def test_expires_is_used_when_ends_is_absent(monkeypatch):
    monkeypatch.setattr(kin_sources, "_get", _router({
        "/points/": POINT_RESPONSE, "/hourly": FORECAST_RESPONSE,
        "/alerts/active": {"features": [_alert_feature(
            ends=None, expires="2026-10-31T12:00:00-04:00")]},
    }))
    data = get_weather(42.672, -83.218, "Troy (approx.)")
    assert len(assess_alerts(sample_commitments(), data["alerts"], 45)) == 1


# ------------------------------------------------------ location guard (T09)
def test_weather_matches_location_detects_a_stale_city():
    data = {"city": "Troy (approx.)"}
    assert weather_matches_location(data, "Troy (approx.)")
    assert not weather_matches_location(data, "Pontiac (approx.)")
    assert not weather_matches_location(None, "Troy (approx.)")


def test_every_city_has_distinct_coordinates():
    coordinates = list(kin_sources.CITIES.values())
    assert len(set(coordinates)) == len(coordinates)


# -------------------------------------------------------------- categorisation
@pytest.mark.parametrize("name,expected", [
    ("Winter Storm Warning", "Winter weather"),
    ("Lake Effect Snow Warning", "Snow"),
    ("Blizzard Warning", "Snow"),
    ("Ice Storm Warning", "Ice"),
    ("Freezing Rain Advisory", "Freezing rain"),
    ("Extreme Cold Warning", "Extreme cold"),
    ("High Wind Advisory", "Strong winds"),
    ("Severe Thunderstorm Warning", "Thunderstorm"),
    ("Flood Watch", "Flooding"),
    ("Dense Fog Advisory", "Fog"),
    ("Special Weather Statement", "Weather alert"),
])
def test_hazard_categories(name, expected):
    assert categorize_hazard(name)[0] == expected


# ------------------------------------------------------------- source registry
def test_official_sources_are_https_oakland_or_weather_gov():
    for source in kin_sources.OU_SOURCES:
        assert source["url"].startswith("https://")
        assert "oakland.edu" in source["url"] or "weather.gov" in source["url"] \
               or "goldengrizzlies.com" in source["url"]


def test_blocked_integrations_are_declared_blocked():
    blocked = {i["name"] for i in kin_sources.INTEGRATION_STATUS
               if i["status"] == "Blocked by authorization"}
    assert any("MySAIL" in name or "Moodle" in name for name in blocked)
    assert any("Push" in name for name in blocked)
