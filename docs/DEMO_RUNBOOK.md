# KIN — Live Demo Runbook (Campus Edition)

**Project:** KIN — Kinetic Intelligence Network  
**Message:** Life changes. KIN moves with you.

This runbook is for the independent, Oakland University-inspired Hacktoberfest demonstration. **All student commitments and simulated weather should be fictional.**

## Before judges arrive (2 minutes)
1. Verify the Streamlit server is reachable on the actual demo device and, if needed, from a second browser.
2. Confirm the sidebar shows **AI ready**, provider **Gemma 4**; *configured* does not prove a live inference works.
3. Verify the exact time and title of an official OU event from its source link.
4. Switch to **Today** and ensure the sample workspace has fictional commitments.
5. Use the **Show me around** expander or the large four-step controls. Keep demo date October 30, 2026.
6. Ensure the public demo displays the warning against uploading private records. For public demo, keep `KIN_PUBLIC_DEMO=1`.
7. Rehearse one actual Gemma-backed response. If it fails, say **non-AI fallback** rather than claiming AI worked.

## The 90-second walkthrough

| Time | Click | Say |
| --- | --- | --- |
| 0–15 sec | Today / hero | “A student has one day but several disconnected sources: classes, weather, work and campus events. KIN connects them.” |
| 15–32 sec | **1 · Plan** | “Gemma 4 converts natural-language fictional commitments into validated proposed calendar entries; the user must approve.” |
| 32–53 sec | **2 · Weather** | “KIN retrieves official NWS data. A clearly **SIMULATED** winter warning demonstrates how the Ripple Engine finds an overlap with an exam commute. KIN cannot independently cancel classes.” |
| 53–72 sec | **3 · Discover** | “KIN checks a source-linked Golden Grizzlies athletics event against this student's timetable, including a planning buffer.” |
| 72–90 sec | **4 · Approve** | “KIN asks before writing the event and verifies the action. The AI explains, but the person decides.” |

## Proof points for technical questions

- `kin_core.py`: deterministic overlapping windows, event validation, dependency/simulation functions.
- `kin_ai.py`: real Gemma-backed extraction, briefing and Q&A; fallback labels preserve honesty.
- `kin_sources.py`: NWS status plus official source provenance.
- `kin_store.py`: local SQLite, approvals and read-back verification.
- `kin_calendar.py`: .ics import/export (private uploads disabled by default for public demo).
- `tests/`: offline tests; do not quote a hard-coded total without running the latest suite.

## Critical safe phrases

- “This is **simulated weather**, used for reproducibility; the displayed live NWS data is separate.”
- “KIN identifies a possible schedule impact, not a road-safety decision.”
- “No verified OU closure has been found by this demonstration.”
- “This is a hackathon prototype, not an official Oakland University application.”
- “The public demo uses fictional data and has no true multi-user authentication or isolation.”

## If the live demo breaks

- **NWS unavailable:** Show a cached timestamp only if present; never say there are no alerts.
- **Gemma unavailable:** Use the visibly labeled deterministic fallback; show code proving Gemma integration and test logs if previously recorded.
- **Live URL unavailable:** Run `python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8502` locally on your demo laptop and present from localhost. External access still requires appropriate networking permissions.
- **Data altered:** Restore the fictional sample data in a safe local instance; don't claim data was restored without verifying the screen.
- **Time is short:** Show Today → Weather → Discover → Approve, then summarize the Gemma integration instead of adding new features.

## Before merging this branch

- Verify all Python tests and syntax checks from the pull request workflow.
- Inspect the browser view at mobile and desktop widths.
- Verify callback navigation and browser refresh.
- Confirm public demo mode disables .ics upload.
- Ensure final metallic KIN logo asset is installed through a separate approved image-file update; CSS fallback is not the identical final logo.

## Deployment note
`KIN_PUBLIC_DEMO=1` blocks private calendar file uploads, but **does not provide user authentication, per-user database separation or data protection**. Keep access limited to controlled synthetic demonstrations; do not use as a public beta for actual users.
