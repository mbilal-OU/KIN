# Architecture

## Principle

> Rules decide. The model explains.

Anything presented to the user as a fact — that two events overlap, that an
alert window touches a commitment, that a source is official — is computed by
deterministic Python in `kin_core.py` or retrieved with provenance by
`kin_sources.py`. Gemma 4 receives already-decided structured evidence and
turns it into prose. It has no tools, no write access, and no authority.

## Layers

```text
┌─────────────────────────────────────────────────────────────┐
│ app.py            Streamlit screens, orchestration, consent │
├─────────────────────────────────────────────────────────────┤
│ kin_ai.py         Gemma calls, extraction, labeled fallback  │
│ kin_core.py       deterministic rules (pure functions)       │
├─────────────────────────────────────────────────────────────┤
│ kin_sources.py    NWS client, OU registry, curated events    │
│ kin_calendar.py   iCalendar import / export                  │
│ kin_store.py      local SQLite persistence                   │
├─────────────────────────────────────────────────────────────┤
│ kin_models.py     shared types, factories, event taxonomy    │
│ kin_theme.py      presentation only (CSS + HTML helpers)     │
└─────────────────────────────────────────────────────────────┘
```

Dependencies point downward only. `kin_core.py` imports nothing that performs
I/O, which is why it is cheap and total to test.

## The agent loop

The directive's `OBSERVE → NORMALIZE → ANALYZE → PLAN → APPROVE → EXECUTE →
VERIFY → LEARN` maps onto the code as:

| Phase | Implementation |
|---|---|
| Observe | `kin_sources.get_weather`, `load_events`, manual entry, `.ics` import |
| Normalize | `kin_models.make_commitment`, `kin_calendar.parse_ics`, offset-aware ISO strings everywhere |
| Analyze | `assess_alerts`, `assess_opportunities`, `detect_internal_conflicts`, `find_free_windows` |
| Plan | `simulate_change`, `make_action` — a proposal with a stated rationale |
| Approve | Approval Center buttons. Nothing else writes |
| Execute | `kin_store.save_commitment` |
| Verify | `kin_store.commitment_exists` read-back before `VERIFIED` is shown |
| Learn | Explicit preference edits only. No inferred profiling |

## Trust boundaries

**1. Untrusted text → validated data.**
`extract_commitment_from_text` returns a *candidate*. It must survive
`validate_event_proposal`, which checks the title length, that both times carry
an explicit offset, that end follows start, that the duration is under 24 hours,
that `requires_travel` is a real boolean, and — with `strict_michigan=True` —
that the offset is the one America/Detroit actually uses on that date. The user
text is JSON-quoted inside the prompt and the standing rule that it is data
precedes it.

**2. External data carries provenance.**
Every weather response records `city`, `lat`, `lon`, `retrieved_at`, a
per-endpoint status (`retrieved` / `unavailable`) and a classified error kind.
`weather_matches_location` prevents one city's data from being rendered under
another's label. Event records carry `source_url`, `verified_as_of`, `status`
and `end_is_estimated`.

**3. AI output is an explanation, not a command.**
There is no function-calling path from the model to the store. The worst a
hostile model response can do is produce text, or a proposal that fails
validation.

**4. No state change without a click.**
`PROPOSED → APPROVED → EXECUTING → VERIFIED`, with `REJECTED` and `FAILED` as
terminal alternatives. `VERIFIED` requires a successful read-back.

## Time handling

Every stored datetime is an ISO 8601 string with an explicit offset. Naive
datetimes are rejected at the boundary by `parse_dt`. America/Detroit crosses a
DST boundary days after the demo date, so `michigan_offset_for` derives the
correct offset from `zoneinfo` rather than hard-coding `-04:00`, and
`michigan_offset_matches` accepts any representation of the same instant
(including UTC) while rejecting a wrong wall-clock offset.

Overlap is **half-open**: `a.start < b.end and b.start < a.end`. Events that
merely touch are not conflicts.

## Buffers

`effective_window` extends a commitment *backwards* by the planning buffer, and
only when `requires_travel` is true. A remote meeting gets no travel buffer. The
buffer is a user-chosen preparation allowance — explicitly **not** a travel-time
prediction, which KIN has no basis to make from one coordinate.

## Simulation isolation

`simulated_alert()` always carries `is_simulation: True` and
`status: "DEMO_ONLY"`. That flag survives `assess_alerts` into every impact
record, so the UI renders simulated results in a visually distinct dashed
section, suppresses the "NWS source" link for them, and passes
`simulated_alert_included` to the model, whose system prompt requires it to
describe a simulation as a demonstration.

## Persistence

SQLite through the standard library — no new dependency. A connection is opened
per call because Streamlit executes scripts on worker threads and SQLite
connections are not thread-shareable. Schema creation is lazy and keyed by
database path, so correctness never depends on a UI-layer cache.

This is **local single-user storage**. It is not isolation, encryption or
authentication, and the Trust screen says so.

## Caching

`cached_weather` is keyed on `(city, lat, lon, bust)` with a 600 s TTL. **Get
weather** may serve the cache; **Force new fetch** calls `.clear()` and passes a
fresh `bust` value, guaranteeing a real request. The parameter must not start
with an underscore, because Streamlit excludes such parameters from cache keys.

## Known structural limits

- Conflict detection is per workspace. Cross-workspace clashes are not surfaced,
  because showing them would leak one context into another without a permission
  model.
- `RRULE` is not expanded; the first occurrence is imported and flagged.
- The action log is append-only but not tamper-evident.
- `find_free_windows` uses a fixed 08:00–22:00 day.
