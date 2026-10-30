# Integrations

Every adapter reports its own availability, freshness and errors. The app shows
this list on **Settings & Trust** so a user never has to guess what is real.

## Live and verified

### National Weather Service

Public, free, no key. `kin_sources.get_weather`.

```http
GET https://api.weather.gov/points/{lat},{lon}
    -> properties.forecastHourly -> GET that URL
GET https://api.weather.gov/alerts/active?point={lat},{lon}
Headers: User-Agent: <KIN_NWS_USER_AGENT>
         Accept: application/geo+json
```

- Timeout 9 s; errors classified as `timeout`, `network`, `http_<code>`.
- Cached 600 s per city, with an explicit cache-bypassing refresh.
- Returns `city`, `lat`, `lon`, `retrieved_at`, `office`, and a per-endpoint
  status of `retrieved` or `unavailable`.
- A failure never becomes "no alerts". Zero alerts is reported as "0 returned at
  retrieval time".
- Six approximate city points only. KIN never requests device location, and a
  single point does not describe a whole commute route.

Set `KIN_NWS_USER_AGENT` to your own project contact before deploying anywhere
public — the NWS asks API users to identify themselves.

### Gemma 4 via the Gemini API

`kin_ai.py`, model `gemma-4-26b-a4b-it`, SDK `google-genai`.

Four uses: event extraction, daily briefing, weather explanation, and Q&A over
stored state. Every response is tagged with the real provider and model string.
Failures produce a deterministic fallback that announces itself as a fallback.

Free-tier inputs may be used to improve provider services, so **only fictional
demonstration data is sent**, and the user can switch schedule sharing off
entirely.

## Local and functional

### Gemma 4 via Ollama

`KIN_AI_PROVIDER=ollama`, default model `gemma4:e2b`, endpoint
`http://localhost:11434/api/chat`, timeout 70 s, temperature 0.1. Nothing leaves
the machine. Requires `ollama pull gemma4:e2b` and enough RAM.

### Curated OU athletics records

`data/events.json` — hand-verified, with `source_url`, `verified_as_of`,
`status`, and `end_is_estimated`. Only start times are official; end times are
planning estimates and are labeled as such everywhere.

Recheck these records if you run the project after 31 October 2026.

### iCalendar import / export

`kin_calendar.py`, standard library only.

Export writes RFC 5545 with correct line folding and notes estimated end times
in the description. Import handles `SUMMARY`, `DTSTART`/`DTEND`, `TZID`, UTC
`Z`, all-day `VALUE=DATE`, `DURATION`, `STATUS:CANCELLED`, and folded lines;
removes duplicates; normalizes to America/Detroit; and reports every skipped
row instead of guessing. `RRULE` is **not** expanded — the first occurrence is
imported and the count of recurring events is shown.

### Official OU source registry

Nine official links in `kin_sources.OU_SOURCES` (closings, registrar dates,
events calendar, athletics, library, police, recreation, involvement, NWS
Detroit/Pontiac office). KIN **links** to these; it does not ingest or scrape
them, and it stores no opening hours it cannot verify.

### Local SQLite store

`kin_store.py`, stdlib `sqlite3`, file `kin_local.db` (git-ignored, overridable
with `KIN_DB_PATH`). Local single-user storage — not isolation, encryption or
authentication.

## Blocked by authorization

Not built, and declared as such in the app. Each would need the listed
prerequisite before any code is worth writing.

| Integration | Prerequisite |
|---|---|
| Moodle / MySAIL schedule sync | Written university authorization and a supported API. Credential scraping is rejected on principle |
| Google Calendar | Registered OAuth client, verified consent screen, token storage |
| Outlook Calendar | Azure app registration and Graph permissions |
| Push notifications | FCM/APNs credentials and delivery infrastructure |
| SMS | A messaging provider account and consent records |
| Email | A sending domain with SPF/DKIM and bounce handling |
| Live professional sports fixtures | A licensed data feed. KIN ships watch-party templates rather than invented times |
| Automatic OU closure detection | A machine-readable official feed. Inferring closure from weather is explicitly forbidden |
| Multi-user accounts and family sharing | Authentication, authorization, tenant isolation, encryption |

## Adding an adapter

Return a dict carrying, at minimum: the data, a `*_status` of `retrieved` or
`unavailable` per endpoint, a `retrieved_at` timestamp, the identity of what was
requested (so a stale response can be detected), a classified error list, and a
`source_url` per record. Then add a row to `INTEGRATION_STATUS` with an honest
label. Never let a failure read as an absence of risk.
