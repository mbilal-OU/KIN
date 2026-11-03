# Feature status matrix

Status labels follow the implementation directive:

- **WORKING AND VERIFIED** — user flow works and a test or live check proves it
- **IMPLEMENTED BUT UNVERIFIED** — code exists, no end-to-end proof yet
- **PARTIALLY IMPLEMENTED** — a useful subset works, documented gaps remain
- **NOT IMPLEMENTED** — deliberately not built
- **BLOCKED BY EXTERNAL ACCESS** — needs authorization this project lacks

Last verified for the original hackathon build: 30 October 2026, 129 automated tests + 10 live checks passing.

---

## November 2026: free-first life-planning expansion

This section supplements, rather than rewrites, the original hackathon verification. The expanded functionality is independent of Oakland University access and does not require a paid AI model.

| Feature | Status | What actually works / limitation |
|---|---|---|
| No-cost AI-off mode | WORKING AND VERIFIED | `KIN_AI_PROVIDER=off` makes no model requests; optional Google SDK moved to `requirements-ai.txt` |
| Manual repeat entry | WORKING AND VERIFIED | Daily, weekdays or weekly events for 1–12 weeks; DST checks; no live RRULE engine |
| Scheduling mode | WORKING AND VERIFIED | Stored records can be marked fixed, flexible or protected; previous records default to fixed |
| Alternative-slot suggestions | PARTIALLY IMPLEMENTED | Rule-checked candidate times across the user's KIN workspaces by default; no external calendar lookup, verified travel duration or priority reasoning |
| Approval-gated rescheduling | WORKING AND VERIFIED | User approves a proposed move; KIN rechecks it and verifies the stored result |
| Series occurrence editing/cancellation | WORKING AND VERIFIED | Preview and approve one, future or all manual routine records; transactional stale-preview checks; no full RRULE editing/pause-resume |
| Cross-workspace conflict visibility | WORKING AND VERIFIED | On Today, reports clashes across guest-profile workspaces; Resolve conflicts can consider other local workspaces |
| Free-first local questions | WORKING AND VERIFIED | Basic schedule, overlap, available-time, and rescheduling questions; not arbitrary conversation |
| Local daily briefing | WORKING AND VERIFIED | Rule-built summary with no model request when AI is off |
| Voice assistant prototype | PARTIALLY IMPLEMENTED | Push-to-talk microphone, optional local Whisper transcription and eSpeak spoken reply, voice-directed rule-based conflict suggestions; CI uses fake speech engines; actual microphone and local CPU model quality still need device testing and HTTPS deployment |
| AI privacy default | PARTIALLY IMPLEMENTED | New profiles opt out of schedule sharing by default; protected external AI context is minimized, but current guest storage is **not encrypted** |
| OU email, calendar, Moodle, or SSO | BLOCKED BY EXTERNAL ACCESS | Not connected; formal approval and security review required |
| OS alarms, wake word, push notifications, secure personal cloud sync | NOT IMPLEMENTED | Future roadmap tasks |

See [Free-first setup](FREE_FIRST.md), [Development Hub](DEVELOPMENT_HUB.md), and [Roadmap](ROADMAP.md).

---

## Stage 1 — the hackathon MVP

| Feature | Status | Where | Proof |
|---|---|---|---|
| App launches with the model unavailable | WORKING AND VERIFIED | `app.py` | `test_app.py::test_app_starts_without_exception` |
| Every screen renders without error | WORKING AND VERIFIED | `app.py` | `test_every_screen_renders_without_exception` |
| Real Gemma 4 inference with provider label | WORKING AND VERIFIED | `kin_ai.py` | `live_smoke.py` — `gemma-4-26b-a4b-it` |
| Free text → validated event proposal | WORKING AND VERIFIED | `kin_ai.py`, `kin_core.py` | `test_ai.py` (12 cases) |
| Malformed / ambiguous model output refused | WORKING AND VERIFIED | `kin_core.validate_event_proposal` | `test_ai.py::test_non_json_reply_is_rejected` |
| Wrong DST offset refused | WORKING AND VERIFIED | `kin_core.michigan_offset_matches` | `test_strict_validation_rejects_wrong_dst_offset` |
| Live NWS forecast + alerts | WORKING AND VERIFIED | `kin_sources.get_weather` | `live_smoke.py` — office DTX |
| Outage says "unavailable", never "no alerts" | WORKING AND VERIFIED | `kin_sources` | `test_weather.py` (6 failure cases) |
| Labeled SIMULATED warning overlapping the exam | WORKING AND VERIFIED | `kin_core.simulated_alert` | `test_simulated_alert_hits_exam` |
| Simulation never presented as NWS | WORKING AND VERIFIED | `app.py`, `kin_core` | `test_simulation_flag_survives_assessment` |
| OU athletics records with provenance | WORKING AND VERIFIED | `data/events.json` | `test_discover_shows_the_official_event_with_provenance` |
| Estimated end times labeled as estimates | WORKING AND VERIFIED | `data/events.json`, UI badge | `test_estimated_end_time_is_reported_as_such` |
| Conflict check against the timetable | WORKING AND VERIFIED | `kin_core.assess_opportunities` | `test_buffer_size_changes_the_verdict` |
| Approve / Reject with verified result | WORKING AND VERIFIED | `app.py`, `kin_store` | `test_approving_a_proposal_inserts_once_and_verifies` |
| Duplicate approval creates nothing | WORKING AND VERIFIED | `kin_store.find_duplicate` | `test_an_already_added_event_cannot_be_proposed_twice` |
| Action history with verification state | WORKING AND VERIFIED | `kin_store.list_actions` | `test_action_history_is_newest_first` |
| No secrets in tracked files | WORKING AND VERIFIED | `.gitignore`, `.env.example` | `test_provider_status_never_echoes_the_secret` |

### Defects found and fixed during this build

| Defect | Risk | Fix |
|---|---|---|
| Weather stored under one key; switching city showed the previous city's data | Student reads the wrong city's forecast | Response carries `city`/`lat`/`lon`; `weather_matches_location` guards the panel and warns on mismatch |
| "Refresh" replayed the 600 s cache | User believes they forced a fetch that never happened | Separate **Get weather** (cache) and **Force new fetch** (`clear()` + cache-busting key) |
| Cache-bust parameter named `_bust` | Streamlit excludes underscore args from cache keys, so the bust was a no-op | Renamed to `bust` |
| `validate_event_proposal` accepted any offset | Model could emit `-05:00` on an EDT date, shifting an exam by an hour | `strict_michigan=True` for AI input; legacy path unchanged |
| Schema creation sat behind `@st.cache_resource` | A new or erased database never got its tables | Lazy per-path schema guard inside `kin_store._conn` |
| Blank assistant name silently inherited the default | The required "no name" option did not work | Three-way alias convention: `None` inherits, `''` means no name |
| Reissued alerts produced duplicate impact cards | Noisy, looks like several warnings | Dedupe per (commitment, alert), highest severity wins |
| `.ics` import mixed UTC and local strings | Inconsistent stored data | Imported times normalized to America/Detroit |

---

## Stage 2 — core student platform

| Feature | Status | Notes |
|---|---|---|
| Local persistence across restarts | WORKING AND VERIFIED | SQLite via stdlib; `kin_local.db` is git-ignored |
| Workspaces: create, rename, select, delete | WORKING AND VERIFIED | Commitments scoped per workspace; deleting one removes only its items |
| Per-workspace assistant alias, blank allowed | WORKING AND VERIFIED | `None` inherits, `''` = no name |
| Preferences (buffers, transport, teams, quiet hours) | WORKING AND VERIFIED | Persisted; round-trips lists and booleans |
| Event taxonomy (12 types) | WORKING AND VERIFIED | Drives icons and the travel-buffer default |
| Commitment tracker (status lifecycle) | WORKING AND VERIFIED | Canceled/completed items excluded from conflict checks |
| Manual event CRUD | WORKING AND VERIFIED | Add, status change, delete — all logged |
| `.ics` export | WORKING AND VERIFIED | RFC 5545 line folding, estimated-end note |
| `.ics` import with approval preview | WORKING AND VERIFIED | TZID / UTC / all-day / DURATION / CANCELLED; duplicates removed |
| Daily briefing from real state | WORKING AND VERIFIED | Gemma or labeled fallback |
| Opportunity Radar with buffer | WORKING AND VERIFIED | Says "fits your selected calendar", not "you are free" |
| In-app notifications with dedupe + dismiss | WORKING AND VERIFIED | Quiet hours collapse low-importance items |
| Trust & privacy screen | WORKING AND VERIFIED | Integration status, what KIN does not do |
| Data export (JSON) and full erase | WORKING AND VERIFIED | Erase gated behind a confirmation checkbox |
| Assistant Q&A over stored state | WORKING AND VERIFIED | Refuses to answer outside the data |
| What-if simulator | WORKING AND VERIFIED | Pure function; proven not to mutate input |
| Campus resource directory | WORKING AND VERIFIED | 9 official links, no invented hours |
| Activity templates (gaming, work, family, rec) | WORKING AND VERIFIED | Blank blocks, not claimed fixtures |
| Semester archive / transition | NOT IMPLEMENTED | Workspaces give a usable manual equivalent today |
| Recurring event expansion | PARTIALLY IMPLEMENTED | First occurrence imported and flagged; RRULE not expanded |
| Course objects (separate from events) | NOT IMPLEMENTED | Events carry a type; a course entity was not needed for the demo |

---

## Stage 3 — optional life modules

| Feature | Status | Notes |
|---|---|---|
| Work shifts in their own workspace | WORKING AND VERIFIED | `work` event type + Employment workspace; additional personal KIN workspaces can now be checked for clashes |
| Family commitments | WORKING AND VERIFIED | `family` event type + Family workspace |
| Gaming / esports / recreation blocks | WORKING AND VERIFIED | Activity templates |
| Future-Self Simulator | WORKING AND VERIFIED | Move-and-compare with explicit apply step |
| Personal memory with user control | PARTIALLY IMPLEMENTED | Preferences are viewable, correctable, exportable and erasable. No inferred profiling exists, by design |
| Dependency chains (shift follows class) | NOT IMPLEMENTED | `simulate_change` is the groundwork. Inferring personal dependencies without a reliable basis was judged unsafe |
| Real multi-user family sharing | BLOCKED BY EXTERNAL ACCESS | Needs authenticated identities and invitation permissions first |
| Goals tracking | NOT IMPLEMENTED | Out of scope for the deadline |

---

## Stage 4 — advanced integrations

All **BLOCKED BY EXTERNAL ACCESS**, and the app says so on the Trust screen.

| Integration | What is missing |
|---|---|
| Moodle / MySAIL sync | University authorization and a supported API. Scraping was rejected |
| Google / Outlook Calendar | Registered OAuth client, consent screen, token storage |
| Push / SMS / email | Delivery infrastructure and credentials |
| Multi-user accounts | Authentication, authorization, tenant isolation, encryption |
| Live professional sports fixtures | A licensed feed. KIN ships watch-party templates instead of invented times |
| Automatic OU closure detection | A machine-readable official feed. KIN links to the page instead |

---

## Scenario coverage (directive §33)

| Scenario | Status |
|---|---|
| A — Michigan winter and an examination | WORKING AND VERIFIED |
| B — Oakland University sporting event | WORKING AND VERIFIED |
| C — Working student conflict | WORKING AND VERIFIED (`work` type + buffer) |
| D — Gaming and recreation | WORKING AND VERIFIED (templates, existing commitments preserved) |
| E — Research and academic deadlines | WORKING AND VERIFIED (`lab`/`meeting`/`assignment` + briefing) |
| F — Family responsibilities | WORKING AND VERIFIED (`family` type; no employer contact exists) |
| G — User customization | WORKING AND VERIFIED (per-workspace aliases persist) |
| H — Permission and trust | PARTIALLY IMPLEMENTED (AI schedule sharing can be revoked; there is no calendar connector to revoke) |
| I — University graduation | PARTIALLY IMPLEMENTED (delete a workspace, keep preferences; no institutional entitlements exist to expire) |
| J — AI or data failure | WORKING AND VERIFIED (both degrade with labeled honesty) |
