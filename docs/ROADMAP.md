# Roadmap

## Institutional-first product direction — proposed November 2026

**Target:** Explore KIN as a possible **OU-endorsed optional companion for students first and later employees**, contingent on OU INC/stakeholder engagement, UTS review, a consented pilot, accessibility, secure infrastructure and procurement. **No approval, pilot, funding or university-wide adoption is claimed.**

**P0 (now):** Prepare a synthetic-data OU Daily Briefing demo; conduct OU stakeholder discovery; confirm Gemini chat vs API terms; ensure public demo displays unofficial/test-data warnings; rotate any exposed AI keys; restore/verify green CI; map data/permissions/security risk; scope an accessible pilot.

**P1 (after sponsor and reviews):** Determine applicable OU review and ethics requirements; establish testable pilot metrics; build production-grade identities, isolation and encryption if permitted real personal data is involved; evaluate an approved model backend; complete accessibility remediation.

**P2 (after written OU authorization):** Role-specific student, faculty and staff workflows; approved Google Workspace and Moodle/MySAIL connectors; limited departmental deployment; evidence-based institutional procurement discussion.

**Architecture decision:** OU makes Google Gemini available via OU Google accounts, but this **does not** grant KIN API access or approval to process university data. KIN currently uses Gemma 4 via Gemini API, local Ollama or AI-off; an actual Gemini model integration is separately unbuilt.

**New P0 tracking issues:** [#24 OU Daily Briefing](https://github.com/mbilal-OU/KIN/issues/24) · [#25 UTS/data gates](https://github.com/mbilal-OU/KIN/issues/25) · [#26 accessibility](https://github.com/mbilal-OU/KIN/issues/26) · [#27 public demo/key/CI hardening](https://github.com/mbilal-OU/KIN/issues/27).

**New strategy documents:** [OU-first](OU_FIRST_STRATEGY.md) · [Pilot](OU_PILOT_PLAN.md) · [Gemini decision](OU_GEMINI_DECISION.md) · [Institutional readiness](OU_INSTITUTIONAL_READINESS.md). Existing issues [#19](https://github.com/mbilal-OU/KIN/issues/19) and [#21](https://github.com/mbilal-OU/KIN/issues/21) remain the central pilot and Gemini workstreams.

Today's build deliberately stops at a stable, honest demonstration. Everything
below is **not implemented**, listed with the gate that must be satisfied first.

## Shipped (30 October 2026)

Stage 1 MVP complete and Stage 2 largely complete: live NWS weather, real Gemma
4 extraction and briefing, deterministic conflict and impact engine, curated
OU events with provenance, approval-gated verified writes, local persistence,
workspaces, assistant naming, `.ics` import/export, commitment tracker, in-app
notifications, what-if simulator, campus directory, and trust/privacy controls.
See [FEATURES.md](FEATURES.md) for the audited matrix.

## Next month

| Item | Gate |
|---|---|
| Expand `RRULE` into real recurring occurrences | Correct handling of DST boundaries and exceptions, with tests |
| Semester archive and rollover | A course entity distinct from individual events |
| Cross-workspace conflict view | A permission model so one context cannot silently leak into another |
| Dependency chains ("shift follows class") | A reliable basis for the relationship. Inferring it unprompted was judged unsafe |
| Richer campus event ingestion | A public, machine-readable OU calendar feed and its terms of use |
| Small user study with real students | Consent, and honest claims about what KIN can do |
| Accessibility audit against WCAG 2.2 AA | Actual testing with a screen reader and contrast tooling |

## 90 days

| Item | Gate |
|---|---|
| Optional persistent accounts | Authentication, authorization, tenant isolation, encryption at rest |
| Google / Outlook calendar sync | Registered OAuth clients, verified consent screens, secure token storage, a security review |
| Event status rechecking | A source that publishes cancellations in a machine-readable form |
| Postgres migration | A migration path and backup/restore procedure |

## 6 months

| Item | Gate |
|---|---|
| Real notification delivery | Delivery infrastructure, consent records, quiet-hour enforcement that genuinely suppresses sending |
| Monitoring and operations | Error tracking, uptime monitoring, an incident-response plan |
| Workspace isolation for shared use | Invitation-based permissions; private event details must stay private within a household |

## 12 months

| Item | Gate |
|---|---|
| Opt-in Oakland University pilot | University approval and a data-processing agreement |
| Moodle / MySAIL integration | Written institutional authorization and a supported API. Credential scraping stays off the table permanently |
| Employment and family connectors | Research into what those users actually need, plus isolation guarantees |

## Long term

The LifeLoop 2090 concept document describes a user-controlled Life Graph,
Future Radar and Trust Monitor across sixteen life domains. That vision guides
*modularity* — which is why `kin_core` is pure, adapters are swappable, and
workspaces exist — but it does not expand today's scope.

The release posture stays the same at every horizon: **a copilot that requires
approval**, with explicit permissions, visible evidence, and verified actions.

Gates that never move:

- No action with a real-world side effect without an explicit human click.
- No claim that an action succeeded without verifying the result.
- No inferred university or employer decisions.
- No compliance or affiliation claim that has not been independently
  established.
- A model failure degrades to a labeled fallback, never to a confident guess.

---

## KIN 2.0: Ideas, tasks and future life-assistant direction (November 2026)

The existing roadmap above describes the original prototype and its staged technical gates. The team is also tracking a **proposed** broader life-assistant product in [KIN Development Hub](DEVELOPMENT_HUB.md). These issues are **not shipped features or delivery commitments**.

| Priority | Workstream | Tracking issue |
|---|---|---|
| P0 | Privacy boundaries, data separation and consent | [#9](https://github.com/mbilal-OU/KIN/issues/9) |
| P0 | Manual school, work and personal routines | [#10](https://github.com/mbilal-OU/KIN/issues/10) |
| P0 | Safe conflict-resolution recommendations | [#11](https://github.com/mbilal-OU/KIN/issues/11) |
| P1 | Alarms, timers and contextual reminders | [#12](https://github.com/mbilal-OU/KIN/issues/12) |
| P1 | Push-to-talk voice assistant | [#13](https://github.com/mbilal-OU/KIN/issues/13) |
| P1 | Independent email/passkey accounts | [#14](https://github.com/mbilal-OU/KIN/issues/14) |
| P1 | Local-first encrypted storage and optional sync | [#15](https://github.com/mbilal-OU/KIN/issues/15) |
| P1 | Student pilot and OU commercialization evidence | [#19](https://github.com/mbilal-OU/KIN/issues/19) |
| P1 | Evaluate Gemini models as optional AI provider and OU pathway | [#21](https://github.com/mbilal-OU/KIN/issues/21) |
| P2 | OU calendar/class schedule connection | [#16](https://github.com/mbilal-OU/KIN/issues/16) |
| P2 | OU Moodle deadlines and announcements | [#17](https://github.com/mbilal-OU/KIN/issues/17) |
| P2 | OU email access feasibility | [#18](https://github.com/mbilal-OU/KIN/issues/18) |
| P2 | Mobile-first experience | [#20](https://github.com/mbilal-OU/KIN/issues/20) |

**Launch order:** Manual entry and .ics import first. Official OU integrations are optional, require written institutional authorization and student consent, and must not use password collection or unofficial scraping. KIN should keep private personal routines outside university visibility.

**To contribute an idea or modification:** [Create an issue using the templates](https://github.com/mbilal-OU/KIN/issues/new/choose). All changes, discussion, decisions and completed work are tracked in GitHub Issues and linked pull requests.
