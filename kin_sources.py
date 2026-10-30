"""Public NWS client and official Oakland University source registry.

No university credentials, no authenticated feeds, no scraping of protected
services. Every record returned carries where it came from and when it was
retrieved, so the interface can always show provenance.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from kin_models import SOURCE_BLOCKED, SOURCE_LIVE, SOURCE_LOCAL

DATA_DIR = Path(__file__).parent / "data"

CITIES: dict[str, tuple[float, float]] = {
    "Oakland University campus (approx.)": (42.672, -83.218),
    "Troy (approx.)": (42.6064, -83.1498),
    "Pontiac (approx.)": (42.6389, -83.2910),
    "Auburn Hills (approx.)": (42.6875, -83.2341),
    "Sterling Heights (approx.)": (42.5803, -83.0302),
    "Rochester Hills (approx.)": (42.6584, -83.1499),
}

# Hazard keywords -> plain-language category, used only for grouping/iconography.
HAZARD_CATEGORIES: dict[str, tuple[str, str]] = {
    "snow": ("Snow", "❄️"),
    "blizzard": ("Snow", "❄️"),
    "winter": ("Winter weather", "❄️"),
    "ice": ("Ice", "\U0001F9CA"),
    "freezing": ("Freezing rain", "\U0001F9CA"),
    "cold": ("Extreme cold", "\U0001F976"),
    "chill": ("Extreme cold", "\U0001F976"),
    "wind": ("Strong winds", "\U0001F4A8"),
    "thunder": ("Thunderstorm", "⛈️"),
    "tornado": ("Tornado", "\U0001F32A️"),
    "flood": ("Flooding", "\U0001F30A"),
    "heat": ("Heat", "\U0001F321️"),
    "fog": ("Fog", "\U0001F32B️"),
}

# Official Oakland University pages. KIN links to these; it does not ingest them.
OU_SOURCES: list[dict[str, str]] = [
    {"name": "OU Campus Closings & Emergency Management",
     "url": "https://www.oakland.edu/police/emergency-management/campus-closings/",
     "category": "Emergency information",
     "note": "The only authoritative source for class cancellation or campus closure."},
    {"name": "OU Registrar — Important Dates",
     "url": "https://www.oakland.edu/registrar/important-dates/",
     "category": "Academic resources",
     "note": "Semester start/end, withdrawal and exam period dates."},
    {"name": "Oakland University Events Calendar",
     "url": "https://calendar.oakland.edu/",
     "category": "Campus events",
     "note": "Public campus event listings."},
    {"name": "Oakland Golden Grizzlies Athletics",
     "url": "https://goldengrizzlies.com/",
     "category": "Athletics",
     "note": "Official schedules, scores and ticket information."},
    {"name": "Kresge Library",
     "url": "https://library.oakland.edu/",
     "category": "Academic resources",
     "note": "Study spaces, research help and hours."},
    {"name": "OU Police Department",
     "url": "https://www.oakland.edu/police/",
     "category": "Campus safety",
     "note": "Campus safety services and emergency contacts."},
    {"name": "Recreation & Well-Being",
     "url": "https://www.oakland.edu/recwell/",
     "category": "Recreation",
     "note": "Recreation centre programmes and facilities."},
    {"name": "Student Organizations (GrizzOrgs)",
     "url": "https://www.oakland.edu/involvement/",
     "category": "Student organizations",
     "note": "Clubs, involvement and student life."},
    {"name": "National Weather Service — Detroit/Pontiac",
     "url": "https://www.weather.gov/dtx/",
     "category": "Emergency information",
     "note": "Official forecast office for the Oakland University area."},
]

# Integrations that exist in the design but are deliberately switched off.
INTEGRATION_STATUS: list[dict[str, str]] = [
    {"name": "National Weather Service API", "status": SOURCE_LIVE,
     "detail": "Public API, no key required. Forecast and active alerts."},
    {"name": "Curated OU athletics records", "status": SOURCE_LOCAL,
     "detail": "Hand-verified JSON seed file with official source links."},
    {"name": "Gemma 4 (Gemini API)", "status": SOURCE_LIVE,
     "detail": "Requires a local GEMINI_API_KEY. Falls back to deterministic text."},
    {"name": "iCalendar (.ics) import/export", "status": SOURCE_LOCAL,
     "detail": "Reads and writes standard .ics files on this machine."},
    {"name": "Moodle / MySAIL account sync", "status": SOURCE_BLOCKED,
     "detail": "Requires university authorization that this project does not have."},
    {"name": "Google / Outlook Calendar OAuth", "status": SOURCE_BLOCKED,
     "detail": "Requires registered OAuth credentials and a consent screen."},
    {"name": "Push / SMS / email delivery", "status": SOURCE_BLOCKED,
     "detail": "No delivery infrastructure. In-app notifications only."},
]


def _get(url: str) -> dict:
    headers = {
        "User-Agent": os.getenv("KIN_NWS_USER_AGENT", "KIN-Hackday-Demo (educational project)"),
        "Accept": "application/geo+json",
    }
    response = requests.get(url, headers=headers, timeout=9)
    response.raise_for_status()
    return response.json()


def categorize_hazard(event_name: str) -> tuple[str, str]:
    lowered = (event_name or "").lower()
    for keyword, category in HAZARD_CATEGORIES.items():
        if keyword in lowered:
            return category
    return ("Weather alert", "⚠️")


def _classify_error(exc: Exception) -> str:
    if isinstance(exc, requests.Timeout):
        return "timeout"
    if isinstance(exc, requests.ConnectionError):
        return "network"
    if isinstance(exc, requests.HTTPError):
        code = getattr(exc.response, "status_code", "?")
        return f"http_{code}"
    return type(exc).__name__.lower()


def get_weather(lat: float, lon: float, city: str = "") -> dict:
    """Return forecast and alerts with freshness/status.

    The response records the city label and coordinates that produced it so the
    interface can never display one location's weather under another's name.
    An API failure is reported as 'unavailable' and is never treated as proof
    that no warnings exist.
    """
    retrieved = datetime.now(timezone.utc).isoformat()
    output: dict[str, Any] = {
        "city": city,
        "lat": lat,
        "lon": lon,
        "retrieved_at": retrieved,
        "forecast": [],
        "alerts": [],
        "errors": [],
        "error_kinds": [],
        "forecast_status": "unavailable",
        "alerts_status": "unavailable",
        "office": "",
    }
    try:
        point = _get(f"https://api.weather.gov/points/{lat},{lon}")
        properties = point.get("properties", {})
        output["office"] = properties.get("cwa", "") or ""
        forecast = _get(properties["forecastHourly"])
        output["forecast"] = forecast.get("properties", {}).get("periods", [])[:12]
        output["forecast_status"] = "retrieved"
    except (requests.RequestException, KeyError, ValueError, TypeError) as ex:
        kind = _classify_error(ex)
        output["error_kinds"].append(kind)
        output["errors"].append(f"Hourly forecast unavailable ({kind}).")
    try:
        raw = _get(f"https://api.weather.gov/alerts/active?point={lat},{lon}")
        alerts = []
        for feature in raw.get("features", []):
            p = feature.get("properties", {})
            name = p.get("event", "Weather alert")
            category, icon = categorize_hazard(name)
            alerts.append({
                "event": name,
                "severity": p.get("severity", "Unknown"),
                "certainty": p.get("certainty", "Unknown"),
                "urgency": p.get("urgency", "Unknown"),
                "headline": p.get("headline", ""),
                "description": (p.get("description", "") or "")[:1500],
                "onset": p.get("onset"),
                "effective": p.get("effective"),
                "ends": p.get("ends"),
                "expires": p.get("expires"),
                "category": category,
                "icon": icon,
                "source_url": p.get("web") or p.get("@id") or feature.get("id")
                              or "https://www.weather.gov/",
                "is_simulation": False,
            })
        output["alerts"] = alerts
        output["alerts_status"] = "retrieved"
    except (requests.RequestException, KeyError, ValueError, TypeError) as ex:
        kind = _classify_error(ex)
        output["error_kinds"].append(kind)
        output["errors"].append(f"NWS alerts unavailable ({kind}).")
    return output


def weather_matches_location(data: dict | None, city: str) -> bool:
    """Guard against showing a previous city's weather under a new label."""
    return bool(data) and data.get("city") == city


def load_events() -> list[dict[str, Any]]:
    """Curated, source-linked opportunity records."""
    path = DATA_DIR / "events.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    for record in records:
        record.setdefault("end_is_estimated", True)
        record.setdefault("category", "sports")
        record.setdefault("organizer", "Oakland University")
    return records


def load_activity_templates() -> list[dict[str, Any]]:
    """Blank activity blocks the user schedules themselves.

    These are templates, never claimed fixtures: KIN holds no live professional
    sports schedule.
    """
    path = DATA_DIR / "activity_templates.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def load_campus_resources() -> list[dict[str, str]]:
    """Campus directory (plan Module R). Static verified links, no live hours."""
    path = DATA_DIR / "campus_resources.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return OU_SOURCES
