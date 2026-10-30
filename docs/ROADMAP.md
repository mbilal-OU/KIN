# Roadmap

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
