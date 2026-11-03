# KIN Free-First Life Planner

**Updated 3 November 2026.** This guide describes the independent, no-cost-AI workflow in KIN. It does **not** mean free hosting, production security, or official Oakland University integration.

## Run without any AI API key

1. Install the project requirements and run Streamlit using the README instructions.
2. Copy `.env.example` to `.env` (or use equivalent environment variables).
3. Set `KIN_AI_PROVIDER=off`. No Gemini API key is needed.
4. Open **Planner → Add manually** to create a timetable or repeating routine.
5. Open **Planner → Resolve conflicts** for suggested available time slots.
6. Ask basic questions such as "Do I have conflicts?", "What is next?", or "When am I free?" in **Ask the assistant**. These answers are local, deterministic, and limited to stored workspace data.

Python and SQLite handle the planner. **No AI request is made when the provider is off.**

## What's implemented

| Feature | Current behavior | Limits |
|---|---|---|
| Manual events | Add, change status, delete, search and export .ics | No institutional write access |
| Repeated routines | Expand daily, weekday or weekly repeats into individual events for 1–12 weeks | Not a complete RRULE engine; edit/delete one occurrence at a time |
| Scheduling categories | Mark a stored event **fixed**, **flexible** or **protected** | Older records default to fixed until changed |
| Conflict detection | Deterministic overlap checking in current workspace | Other workspaces and outside calendars not considered |
| Conflict suggestions | Find free options for a **flexible** event using 15-minute slots | Only 7 AM–10 PM; next 3, 7 or 14 days; no travel ETA or priority inference |
| Move approval | Explicit button; proposal rechecked and stored result verified | Only edits KIN's local record |
| Rule-based questions | Recognize common schedule, conflict, available-time and rescheduling questions | Not a general-purpose conversational model |
| Daily briefing | Can produce a local rule-built summary | Less flexible language than AI explanations |
| AI privacy | External AI schedule sharing is **off by default** for new profiles | Cloud AI remains opt-in and not suitable for sensitive data without further review |

## Schedule behavior and safety

- A **fixed** class, exam or employer shift is not offered as an automatically movable commitment. To change a local copy, the user must explicitly edit it.
- **Protected** commitments reserve time and block proposed alternative slots.
- **Flexible** routines can be suggested for movement; KIN never changes them silently.
- The optional spacing buffer is a user preference, not a commute prediction.
- Suggestions consider only one selected workspace. A candidate may still collide with events elsewhere. No claim of complete conflict elimination is made.
- Repeating routines are **separate saved events**, not subscriptions or synchronized series. The demo does not currently support pausing/editing an entire series at once.
- DST-invalid local times are refused rather than silently adjusted.
- Calendar entries may include **fictional October 2026 demonstration data**. The home screen now follows the actual Michigan calendar date, and manual entry defaults to today.

## Optional AI providers

- `KIN_AI_PROVIDER=off` (default in example): **No AI requests**; deterministic planner and answers.
- `KIN_AI_PROVIDER=ollama`: Optional local Gemma model; no per-request hosted API charge, but requires computing resources.
- `KIN_AI_PROVIDER=gemini`: Optional hosted Gemma 4 via the Gemini API. First install `python -m pip install -r requirements-ai.txt`, then supply your own credentials. An eligible model and acceptance of current terms are required. **Free tier and quotas are not guaranteed**, and this is not OU's Gemini chat entitlement.

Current KIN uses **Gemma 4 via the Gemini API** as an optional model backend. It does not automatically have access to Google's separate Gemini models merely because OU offers the Gemini chat app.

## Privacy and deployment boundaries

**This remains a prototype.** The current local SQLite store is not encrypted, authenticated or ready for multiple university users. On a hosted deployment, KIN's session databases are separated, but the server still processes inputs and may lose them on restart. Treat public deployments as **fictional-data demonstrations** only. The user-controlled data export and erase functions remain available.

Do not enter personal or OU-restricted records in public GitHub issues. Do not collect OU login credentials or scrape Moodle/MySAIL. Any authorized OU integration requires university approval, consent and security review.

## Planned, not shipped

OS-level alarms and push notifications, real voice assistant, passkey/email accounts, encrypted local-first storage, cross-workspace planning, true recurring-series editing, Moodle, OU mail/calendar sync, and a production OU pilot are separately tracked in the [Development Hub](DEVELOPMENT_HUB.md). See [Roadmap](ROADMAP.md).

## Verify locally

```bash
python -m compileall -q app.py kin_life.py kin_core.py kin_models.py kin_ai.py kin_store.py
python -m pytest -q
```

The test suite must run without sending AI requests or using any API key. GitHub Actions also runs an offline syntax and test check on pushes.
