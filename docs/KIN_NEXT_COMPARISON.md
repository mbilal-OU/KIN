# KIN NEXT — side-by-side design prototype

This is a **separate** Streamlit entry point: `kin_next.py`.

The existing `app.py`, live deployment on port 8503, SQLite store, and current product remain unchanged.

## Run alongside the existing app

```bash
git fetch origin prototype/kin-next-interactive
git switch prototype/kin-next-interactive
python -m pip install -r requirements.txt
python -m streamlit run kin_next.py --server.port 8504
```

Visit `http://localhost:8504`. For a network-hosted comparison, use `--server.address 0.0.0.0` only if your server is properly secured and the port is allowed.

To return to the original project: `git switch main`, then run the original `app.py`. **Do not merge the prototype until both designs have been compared.**

## What's interactive

- **Overview:** action-first dashboard, synthetic timeline, navigation shortcuts, responsive dark-gold design.
- **My planner:** create, review, approve, and remove commitments in this browser session.
- **Weather intelligence:** request official NWS data for approximate Michigan locations; clearly labeled fictional storm and deterministic schedule-impact matching.
- **Campus life:** source-linked OU athletics event examples; conflict checks and approval-based additions.
- **Ask KIN:** real Gemma provider integration when configured and when the user explicitly consents to sending the fictional schedule; otherwise a clearly labeled deterministic fallback.
- **Settings:** planning buffer, reset and transparent trust boundaries.

## Isolation and limitations

- Does **not** import `kin_store`, read the original `kin_local.db`, or change `app.py`.
- Session-state demo only: it is not durable, authenticated, or isolated against server administrators.
- Uses the existing `kin_core`, `kin_ai`, `kin_sources`, and `kin_models` modules for real logic.
- Weather network requests are triggered by a user action; outages are shown as unavailable.
- Fictional storm and timetable are not real safety alerts or university decisions.
- OU events are curated examples, not a real-time campus event feed.
- The Gemma response is only shown as model-generated when an actual model call succeeds.
- No production-grade identity, privacy controls, or push notifications.

## Test

```bash
python -m pytest -q tests/test_kin_next.py
python -m compileall -q kin_next.py
```

Test startup and interactions manually on a desktop and phone before a live demonstration. The GitHub workflow checks Python startup and core simulation, but cannot validate an actual browser session, the deployed port, or a paid API integration.

## Compare before deciding

1. Keep original on `8503`, run NEXT on `8504`.
2. Compare first impression, mobile layout, navigation and onboarding.
3. Test manual event approval, simulation, NWS unavailable behavior, campus discovery and AI opt-in.
4. Decide whether to keep the original, adopt NEXT, or merge selected design elements.
