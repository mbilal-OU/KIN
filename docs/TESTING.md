# Testing

```bash
python -m pytest -q                 # 129 tests, ~7 s, no network, no quota
python -m pytest -q tests/test_app.py   # interface only
python tests/live_smoke.py          # MANUAL: real NWS + real Gemma
```

The automated suite mocks every external call, so it is safe in CI and cannot
spend API quota. `tests/live_smoke.py` is intentionally **not** named `test_*`
so pytest never collects it.

## Layout

| File | Tests | Covers |
|---|---|---|
| `tests/test_core.py` | 25 | Overlap, buffers, DST, impact dedupe, free windows, simulator |
| `tests/test_weather.py` | 26 | NWS success and every failure mode, location guard, hazard categories |
| `tests/test_ai.py` | 27 | Extraction, malformed output, injection, provider status, fallback labeling |
| `tests/test_store.py` | 29 | Persistence, workspace isolation, approval lifecycle, `.ics` |
| `tests/test_app.py` | 22 | Real `app.py` execution via Streamlit `AppTest` |

`test_app.py` runs the actual application with Streamlit's `AppTest` harness
against a temporary database and a deliberately invalid API key. It catches
runtime errors that module-level unit tests cannot — it is what found the schema
caching defect and the blank-assistant-name defect.

## Directive test matrix

| ID | Requirement | Test |
|---|---|---|
| T01 | Events overlapping by 30 min conflict | `test_overlap_positive` |
| T02 | Touching events do not conflict | `test_touching_events_are_not_conflicts` |
| T03 | Naive timestamps rejected | `test_model_proposal_rejects_unzoned_dates` |
| T04 | DST-aware EDT/EST offsets | `test_michigan_offset_differs_across_dst_boundary`, `test_strict_validation_*` |
| T05 | Fake 06:30–12:00 warning hits the 9 AM exam | `test_simulated_alert_hits_exam` |
| T06 | Remote meeting gets no travel buffer | `test_remote_commitment_gets_no_travel_buffer` |
| T07 | 200 with zero alerts is "retrieved", not "safe" | `test_zero_alerts_is_a_retrieved_result_not_a_failure` |
| T08 | Timeout gives no clean bill of health | `test_alert_timeout_reports_unavailable_and_never_implies_safety` |
| T09 | City change cannot show stale data | `test_weather_matches_location_detects_a_stale_city` |
| T10 | Valid model JSON validated, not inserted | `test_valid_model_output_becomes_a_validated_proposal`, `test_proposing_an_event_stores_nothing_until_approved` |
| T11 | Invalid JSON or wrong time refused | `test_non_json_reply_is_rejected`, `test_reversed_times_are_rejected_by_validation` |
| T12 | Prompt injection treated as data | `test_injected_instructions_cannot_smuggle_an_event_past_validation` |
| T13 | Rejection leaves the calendar unchanged | `test_rejecting_a_proposal_leaves_the_timetable_untouched` |
| T14 | Approval inserts one verified event | `test_approving_a_proposal_inserts_once_and_verifies` |
| T15 | Repeated approval creates no duplicate | `test_an_already_added_event_cannot_be_proposed_twice` |
| T16 | Estimated end time clearly labeled | `test_estimated_end_time_is_reported_as_such`, `test_discover_shows_the_official_event_with_provenance` |
| T17 | Missing key gives a labeled fallback | `test_provider_status_reports_missing_key_*`, `test_missing_api_key_is_shown_as_not_configured` |
| T18 | NWS warning never becomes a closure claim | `test_briefing_fallback_reports_real_counts_and_no_closure_claim` |
| T19 | Blank name gives neutral wording | `test_blank_assistant_name_falls_back_to_a_neutral_phrase` |
| T20 | No secrets in tracked files | `test_provider_status_never_echoes_the_secret` + the `git ls-files` check in SECURITY.md |

## Manual checklist before demonstrating

1. `python -m pytest -q` → 129 passed.
2. `python tests/live_smoke.py` → 10/10, and note the printed model label.
3. `streamlit run app.py` → <http://localhost:8501>.
4. Sidebar: clear the assistant name → header reads "your companion". Type one →
   it persists after a page refresh.
5. Planner → Extract with Gemma 4 → the sample sentence → a proposal appears but
   the timetable does not change until **Approve and add**.
6. Michigan Weather → **Get weather** → check the retrieval timestamp and alert
   count wording. Switch city without refetching → the stale-data warning
   appears. **Force new fetch** → timestamp updates.
7. Toggle the SIMULATED warning → it renders in its own dashed section and the
   impact card is badged "simulated — not NWS" with no NWS source link.
8. Discover OU → the volleyball card shows its source, verification date and
   "end time estimated" → **Propose adding**.
9. Approvals & History → **Approve and add** → success states the write was
   verified; history shows `VERIFIED`. Return to Discover → the button is now
   disabled.
10. Settings & Trust → confirm blocked integrations are listed, export the JSON,
    then erase and confirm the demo seed returns.

## Not covered by automated tests

- Visual appearance, colour contrast ratios, and screen-reader behaviour
  (WCAG 2.2 AA is a target, not an audited result).
- Live Gemma output *quality* — only that a response arrives, carries its real
  provider label, and avoids closure language.
- Real NWS alert content, which depends on actual Michigan weather.
- Concurrent multi-process access to the SQLite file.
- Browser-level behaviour; `AppTest` exercises the script, not a real browser.
