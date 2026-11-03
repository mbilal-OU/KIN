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
| Repeated routines | Expand repeats into separate occurrences and preview edits or cancellations for one, future or all occurrences | Still not a full RRULE engine; no automatic exception or pause/resume model |
| Scheduling categories | Mark a stored event **fixed**, **flexible** or **protected** | Older records default to fixed until changed |
| Conflict detection | Deterministic checks within a workspace and across this guest profile's KIN workspaces | Other users and external calendars not considered |
| Conflict suggestions | Find free slots for a **flexible** event across KIN workspaces by default (optional toggle) | Only 7 AM–10 PM; next 3, 7 or 14 days; no travel ETA or priority inference |
| Move approval | Explicit button; proposal rechecked and stored result verified | Only edits KIN's local record |
| Rule-based questions | Recognize common schedule, conflict, available-time and rescheduling questions | Not a general-purpose conversational model |
| Daily briefing | Can produce a local rule-built summary | Less flexible language than AI explanations |
| AI privacy | External AI schedule sharing is **off by default** for new profiles | Cloud AI remains opt-in and not suitable for sensitive data without further review |

## Schedule behavior and safety

- A **fixed** class, exam or employer shift is not offered as an automatically movable commitment. To change a local copy, the user must explicitly edit it.
- **Protected** commitments reserve time and block proposed alternative slots.
- **Flexible** routines can be suggested for movement; KIN never changes them silently.
- The optional spacing buffer is a user preference, not a commute prediction.
- Suggested alternatives now consider **all workspaces in your own KIN guest profile by default**, or the selected workspace if you untick the toggle. External calendars, other people's records and unentered tasks are not considered. No claim of complete conflict elimination is made.
- Repeating routines are **separate saved events**, not subscriptions or synchronized recurrence rules. Use **Planner → Edit routines** to preview updates or cancellations for one occurrence, selected-and-future occurrences or the entire saved series. Canceled entries remain in the local archive. Bulk changes are applied atomically after approval, with stale-preview and duplicate checks.
- KIN shows cross-workspace overlaps only within the current guest profile. Nothing is shared with a university, an employer or other users.
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

OS-level alarms and push notifications, real voice assistant, passkey/email accounts, encrypted local-first storage, full RRULE recurrence exceptions and pause/resume, Moodle, OU mail/calendar sync, and a production OU pilot are separately tracked in the [Development Hub](DEVELOPMENT_HUB.md). See [Roadmap](ROADMAP.md).

## Verify locally

```bash
python -m compileall -q app.py kin_life.py kin_core.py kin_models.py kin_ai.py kin_store.py
python -m pytest -q
```

The test suite must run without sending AI requests or using any API key. GitHub Actions also runs an offline syntax and test check on pushes.
